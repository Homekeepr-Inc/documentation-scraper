from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, PlainTextResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from .db import init_db, fetch_document, search_documents

templates = Jinja2Templates(directory="app/templates")

app = FastAPI(title="Appliance Manuals API")


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
