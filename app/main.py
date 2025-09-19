import sys
import os
import asyncio
import tempfile
import shutil
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, PlainTextResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.responses import JSONResponse

from .db import init_db, fetch_document, search_documents

# Add path for headless scraper
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'headless-browser-scraper'))
from parallelism import enqueue_scrape_job, get_job_result, is_job_complete
from ge.ge_headless_scraper import ingest_ge_manual
from lg.lg_scraper import ingest_lg_manual
from kitchenaid.kitchenaid_headless_scraper import ingest_kitchenaid_manual
from whirlpool.whirlpool_headless_scraper import ingest_whirlpool_manual
from samsung.samsung_headless_scraper import ingest_samsung_manual
from frigidaire.frigidaire_headless_scraper import ingest_frigidaire_manual

templates = Jinja2Templates(directory="app/templates")

def normalize_model(model):
    return model.replace('/', '_')

app = FastAPI(title="Appliance Manuals API")

# Custom header secret for API protection
SCRAPER_SECRET = os.getenv("SCRAPER_SECRET")

@app.middleware("http")
async def check_custom_header(request: Request, call_next):
    header_value = request.headers.get("X-Homekeepr-Scraper")
    if header_value != SCRAPER_SECRET:
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
    response = await call_next(request)
    return response


@app.on_event("startup")
def _startup() -> None:
    init_db()


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
async def scrape_brand_model(brand: str, model: str):
    brand = brand.lower()
    supported_brands = {'ge', 'lg', 'kitchenaid', 'whirlpool', 'samsung', 'frigidaire'}
    if brand not in supported_brands:
        raise HTTPException(status_code=400, detail="Unsupported brand")

    normalized_model = normalize_model(model)

    # Check DB for existing document
    loop = asyncio.get_event_loop()
    from .db import get_db
    doc = await loop.run_in_executor(None, lambda: get_db().execute("SELECT id, local_path FROM documents WHERE brand = ? AND model_number = ? AND local_path IS NOT NULL LIMIT 1", (brand, normalized_model)).fetchone())
    if doc:
        return FileResponse(doc[1], media_type="application/pdf")

    # Not cached, enqueue scrape job
    job_id = enqueue_scrape_job(brand, model)

    # Wait for result
    while not is_job_complete(job_id):
        await asyncio.sleep(0.5)

    result = get_job_result(job_id)

    if isinstance(result, Exception):
        raise HTTPException(status_code=500, detail=f"Scraping failed: {result}")


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

    ingest_result = await loop.run_in_executor(None, ingest_func, result)
    if not ingest_result or not ingest_result.id:
        # Check if already exists
        doc = await loop.run_in_executor(None, lambda: get_db().execute("SELECT id FROM documents WHERE file_url = ?", (result['file_url'],)).fetchone())
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
    doc = await loop.run_in_executor(None, fetch_document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    path = doc.get("local_path")
    if not path:
        raise HTTPException(status_code=404, detail="File not stored locally")
    return FileResponse(path, media_type="application/pdf")












