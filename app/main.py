import sys
import os
import asyncio
import tempfile
import shutil
from typing import Optional

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import FileResponse, PlainTextResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.responses import JSONResponse

from .db import init_db, fetch_document, search_documents

# Add path for headless scraper
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'headless-browser-scraper'))
from ge.ge_headless_scraper import scrape_ge_manual, ingest_ge_manual
from lg.lg_scraper import scrape_lg_manual, ingest_lg_manual
from kitchenaid.kitchenaid_headless_scraper import scrape_kitchenaid_manual, ingest_kitchenaid_manual
from whirlpool.whirlpool_headless_scraper import scrape_whirlpool_manual, ingest_whirlpool_manual
from samsung.samsung_headless_scraper import scrape_samsung_manual, ingest_samsung_manual
from frigidaire.frigidaire_headless_scraper import scrape_frigidaire_manual, ingest_frigidaire_manual
from aosmith.aosmith_headless_scraper import scrape_aosmith_manual, ingest_aosmith_manual
from rheem.rheem_headless_scraper import scrape_rheem_manual, ingest_rheem_manual

templates = Jinja2Templates(directory="app/templates")

def normalize_model(model):
    return model.replace('/', '_')

app = FastAPI(title="Appliance Manuals API")

# Custom header secret for API protection
SCRAPER_SECRET = os.getenv("SCRAPER_SECRET")
if SCRAPER_SECRET == None or SCRAPER_SECRET == "":
    raise ValueError("**Security Violation**: SCRAPER_SECRET is an empty string or null!")



@app.middleware("http")
async def check_custom_header(request: Request, call_next):
    # Bypass header check for health check endpoints (internal)
    if request.url.path in ["/health"]:
        response = await call_next(request)
        return response
    header_value = request.headers.get("X-Homekeepr-Scraper")
    if header_value != SCRAPER_SECRET:
        print(f"header_value: {header_value}")
        print(f"SCRAPER_SECRET {SCRAPER_SECRET}")
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
    response = await call_next(request)
    return response


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}





@app.get("/", response_class=HTMLResponse)
def browse_ui(request: Request, query: Optional[str] = None, brand: Optional[str] = None, doc_type: Optional[str] = None, equipment_category: Optional[str] = None, limit: int = 50):
    documents = search_documents(query=query, brand=brand, doc_type=doc_type, limit=limit)
    # Get unique values for filters
    all_docs = search_documents(limit=1000)
    brands = sorted(set(d['brand'] for d in all_docs if d['brand']))
    doc_types = sorted(set(d['doc_type'] for d in all_docs if d['doc_type']))
    categories = sorted(set(d.get('equipment_category') for d in all_docs if d.get('equipment_category')))
    
    return templates.TemplateResponse("browse.html", {
        "request": request,
        "documents": documents,
        "query": query or "",
        "brand": brand or "",
        "doc_type": doc_type or "",
        "equipment_category": equipment_category or "",
        "brands": brands,
        "doc_types": doc_types,
        "categories": categories,
        "total": len(documents)
    })


@app.get("/documents")
def list_documents(query: Optional[str] = None, brand: Optional[str] = None, doc_type: Optional[str] = None, model: Optional[str] = None, equipment_category: Optional[str] = None, limit: int = 50, offset: int = 0, include_text: bool = False):
    results = search_documents(query=query, brand=brand, doc_type=doc_type, model=model, equipment_category=equipment_category, limit=limit, offset=offset)
    if not include_text:
        for r in results:
            r.pop("text", None)
            r.pop("text_path", None)
    return results


@app.get("/documents/{doc_id}")
def get_document(doc_id: int):
    doc = fetch_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    return doc


@app.get("/documents/{doc_id}/download")
def download_document(doc_id: int):
    doc = fetch_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")
    path = doc.get("local_path")
    if not path:
        raise HTTPException(status_code=404, detail="File not stored locally")
    return FileResponse(path, media_type="application/pdf")


@app.get("/documents/{doc_id}/text")
def get_document_text(doc_id: int):
    import gzip
    import os

    doc = fetch_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Not found")

    text_path = doc.get("text_path")
    if text_path and os.path.exists(text_path):
        with gzip.open(text_path, "rt", encoding="utf-8") as f:
            text = f.read()
        return PlainTextResponse(text)

    text = doc.get("text")
    if text:
        return PlainTextResponse(text)

    raise HTTPException(status_code=404, detail="Text not available")


@app.get("/scrape/{brand}/{model:path}")
def scrape_brand_model(brand: str, model: str):
    brand = brand.lower()
    supported_brands = {'ge', 'lg', 'kitchenaid', 'whirlpool', 'samsung', 'frigidaire', 'aosmith', 'rheem'}
    if brand not in supported_brands:
        raise HTTPException(status_code=400, detail="Unsupported brand")

    normalized_model = normalize_model(model)

    # Check DB for existing document
    from .db import get_db
    try:
        doc = get_db().execute("SELECT id, local_path FROM documents WHERE brand = ? AND model_number = ? AND local_path IS NOT NULL LIMIT 1", (brand, normalized_model)).fetchone()
    except sqlite3.OperationalError as e:
        if "no such table" in str(e):
            raise HTTPException(status_code=503, detail="Database not initialized. Please try again later.")
        raise HTTPException(status_code=500, detail="Database error")
    if doc:
        return FileResponse(doc[1], media_type="application/pdf")

    # Not cached, scrape synchronously
    try:
        if brand == 'ge':
            result = scrape_ge_manual(model)
        elif brand == 'lg':
            result = scrape_lg_manual(model)
        elif brand == 'kitchenaid':
            result = scrape_kitchenaid_manual(model)
        elif brand == 'whirlpool':
            result = scrape_whirlpool_manual(model)
        elif brand == 'samsung':
            result = scrape_samsung_manual(model)
        elif brand == 'frigidaire':
            result = scrape_frigidaire_manual(model)
        elif brand == 'aosmith':
            result = scrape_aosmith_manual(model)
        elif brand == 'rheem':
            result = scrape_rheem_manual(model)
        else:
            result = None
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")

    if not result:
        raise HTTPException(status_code=404, detail="No manual found")

    # Handle case where result is a list (take first result)
    if isinstance(result, list):
        result = result[0]

    # Select ingest function based on brand
    if brand == 'ge':
        ingest_func = ingest_ge_manual
    elif brand == 'lg':
        ingest_func = ingest_lg_manual
    elif brand == 'kitchenaid':
        ingest_func = ingest_kitchenaid_manual
    elif brand == 'whirlpool':
        ingest_func = ingest_whirlpool_manual
    elif brand == 'samsung':
        ingest_func = ingest_samsung_manual
    elif brand == 'frigidaire':
        ingest_func = ingest_frigidaire_manual
    elif brand == 'aosmith':
        ingest_func = ingest_aosmith_manual
    elif brand == 'rheem':
        ingest_func = ingest_rheem_manual

    try:
        ingest_result = ingest_func(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingest failed: {str(e)}")

    if not ingest_result or not ingest_result.id:
        # Check if already exists
        try:
            doc = get_db().execute("SELECT id FROM documents WHERE file_url = ?", (result['file_url'],)).fetchone()
        except sqlite3.OperationalError as e:
            if "no such table" in str(e):
                raise HTTPException(status_code=503, detail="Database not initialized. Please try again later.")
            raise HTTPException(status_code=500, detail="Database error")
        if doc:
            doc_id = doc[0]
        else:
            raise HTTPException(status_code=500, detail="Failed to ingest")
    else:
        doc_id = ingest_result.id

    # Clean up temp directory if it exists
    if result and result.get('local_path'):
        temp_dir = os.path.dirname(result['local_path'])
        scraper_temp_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'headless-browser-scraper', 'temp'))
        temp_dir = os.path.abspath(temp_dir)
        if temp_dir and os.path.exists(temp_dir):
            try:
                # Use commonpath for reliable subdirectory check
                common = os.path.commonpath([scraper_temp_dir, temp_dir])
                if common == scraper_temp_dir:
                    shutil.rmtree(temp_dir)
                    print(f"Cleaned up temp dir: {temp_dir}")
            except (ValueError, OSError) as e:
                print(f"Error cleaning temp dir {temp_dir}: {e}")

    # Serve the file
    doc = fetch_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    path = doc.get("local_path")
    if not path:
        raise HTTPException(status_code=404, detail="File not stored locally")
    return FileResponse(path, media_type="application/pdf")

