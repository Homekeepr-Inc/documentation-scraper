import gzip
import hashlib
import io
import time
from dataclasses import dataclass
from typing import Optional, Tuple

import requests
from langdetect import detect, DetectorFactory
from pdfminer.high_level import extract_text as pdfminer_extract_text
from pypdf import PdfReader

from . import db
from .storage import paths_for
from .logging_config import get_logger
from .exceptions import PDFProcessingError, NetworkTimeoutError

DetectorFactory.seed = 0
logger = get_logger("ingest")


@dataclass
class IngestResult:
    id: Optional[int]
    sha256: str
    pages: int
    size_bytes: int
    english_present: bool


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _extract_text_and_pages(pdf_bytes: bytes) -> Tuple[str, int]:
    text = pdfminer_extract_text(io.BytesIO(pdf_bytes)) or ""
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        pages = len(reader.pages)
    except Exception:
        pages = 0
    return text, pages


def _english_present(text: str) -> bool:
    snippet = text[:10000] if text else ""
    if not snippet.strip():
        return False
    try:
        lang = detect(snippet)
        return lang == "en"
    except Exception:
        return False


def ingest_from_url(brand: str, model_number: str, doc_type: str, title: str, source_url: str, file_url: str, equipment_category: str = "appliance", equipment_type: str = "unknown") -> IngestResult:
    # Speed optimization: Check if we already have this URL
    existing = db.get_db().execute("SELECT file_sha256, pages, size_bytes, english_present FROM documents WHERE file_url = ?", (file_url,)).fetchone()
    if existing:
        logger.info(f"Skipping duplicate URL: {file_url}")
        return IngestResult(id=None, sha256=existing[0], pages=existing[1], size_bytes=existing[2], english_present=bool(existing[3]))
    
    logger.info(f"Downloading PDF: {file_url}")
    http_status = 200  # Default for local files
    if file_url.startswith('/'):
        with open(file_url, 'rb') as f:
            pdf_bytes = f.read()
    else:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/pdf,*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': source_url,
        }
        resp = requests.get(file_url, headers=headers, timeout=20, stream=True)  # Increased timeout and stream
        resp.raise_for_status()
        http_status = resp.status_code
        pdf_bytes = resp.content
    size_bytes = len(pdf_bytes)
    sha = _sha256_bytes(pdf_bytes)
    

    text, pages = _extract_text_and_pages(pdf_bytes)
    english = _english_present(text)

    pdf_path, text_path = paths_for(brand, model_number, doc_type, sha, equipment_category)
    if not pdf_path.exists():
        pdf_path.write_bytes(pdf_bytes)
    if text:
        with gzip.open(text_path, "wt", encoding="utf-8") as f:
            f.write(text)

    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    doc = {
        "brand": brand.lower(),
        "model_number": model_number,
        "doc_type": doc_type,
        "equipment_category": equipment_category,
        "equipment_type": equipment_type,
        "title": title,
        "language": "en" if english else None,
        "published_at": None,
        "source_url": source_url,
        "file_url": file_url,
        "file_sha256": sha,
        "size_bytes": size_bytes,
        "pages": pages,
        "ocr_applied": 0,
        "english_present": 1 if english else 0,
        "status": "ok",
        "http_status": http_status,
        "local_path": str(pdf_path),
        "text_path": str(text_path),
        "text": text,
        "ingested_at": now,
        "last_seen_at": now,
    }

    doc_id = db.insert_or_ignore_document(doc)
    return IngestResult(id=doc_id, sha256=sha, pages=pages, size_bytes=size_bytes, english_present=english)
