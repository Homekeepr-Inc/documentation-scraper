# Manual Ingest Endpoint

**Date:** 2026-02-19
**Scope:** documentation-scraper repo — one new endpoint in `app/main.py`
**Companion doc:** `temporal-jobs/system_design/2026-02-19-scrape-retry-self-healing.md`

---

## Why this matters

The scraper can't find manuals for every appliance. When it returns 404, the Temporal workflow retries on a backoff schedule (see companion doc), but some manuals will never be auto-scraped — the manufacturer doesn't publish them online, the scraper doesn't support that site, etc. A Homekeepr admin who manually finds the PDF needs a way to inject it into the scraper's database so the next retry picks it up automatically.

Without this endpoint, there's no way to seed a manual into the system short of SSH'ing into the VPS and running SQL against the SQLite database.

---

## How it works

### New endpoint: `POST /ingest/{brand}/{model}`

Accepts a multipart PDF upload. Validates it, writes it to blob storage, inserts into SQLite, and returns the document metadata. After this, `GET /scrape/{brand}/{model}` will find the cached document and return it immediately — no web scraping needed.

### Why this works with zero Temporal changes

The Temporal activity `fetchManualFromScraper` calls `GET /scrape/{brand}/{model}`. That endpoint checks the SQLite cache first (`_get_cached_local_path`). If a row exists for that brand/model with a `local_path`, it returns the file directly. So seeding the database via `POST /ingest` is all that's needed — the next scrape attempt finds the cached PDF.

---

## Implementation

### Endpoint

```python
@app.post("/ingest/{brand}/{model:path}")
async def ingest_manual_upload(brand: str, model: str, file: UploadFile):
```

### Steps

1. **Validate inputs** — brand is lowercased, model is normalized with `normalize_model()` (replaces `/` with `_`), file must be present
2. **Check for existing document** — query SQLite for `(brand, model_number, doc_type='owner')`. If it already exists, return the existing document metadata (same dedup behavior as `ingest_from_local_path`)
3. **Save PDF to temp file** — write the upload to a temp file via `create_temp_download_dir()` / `cleanup_temp_dir()` (existing helpers in `utils.py`)
4. **Validate PDF** — call `validate_pdf_file()` (existing helper) to confirm it's a real PDF (checks `%PDF-` magic bytes). Reject with 400 if invalid.
5. **Ingest** — call `validate_and_ingest_manual()` with a result dict:
   ```python
   result = {
       "brand": brand,
       "model_number": normalized_model,
       "doc_type": "owner",
       "title": f"{brand} {model} Owner's Manual (admin upload)",
       "source_url": "admin_upload",
       "file_url": "admin_upload",
       "local_path": temp_pdf_path,
   }
   ```
   This reuses the existing ingestion pipeline: hashes the PDF, extracts text, detects language, writes to blob storage (`paths_for`), inserts into SQLite via `insert_or_ignore_document`.
6. **Clean up temp file** — `cleanup_temp_dir()`
7. **Return** — 200 with the document metadata (id, sha256, pages, size_bytes, english_present)

### Auth

The `/ingest` endpoint requires a **separate secret** from the scraper's general `X-Homekeepr-Scraper` header. This endpoint must only be callable by the temporal-jobs admin API, not by anything that happens to know the scraper secret.

**`X-Homekeepr-Ingest` header** — a dedicated secret loaded from `SCRAPER_INGEST_SECRET` env var. The `/ingest` endpoint bypasses the general `X-Homekeepr-Scraper` middleware and checks only `X-Homekeepr-Ingest`. The two secrets are completely independent — knowing one doesn't help with the other.

The existing `check_custom_header` middleware is updated to skip `/ingest` paths (same as it skips `/health` and `/status`). The endpoint handler checks `X-Homekeepr-Ingest` itself.

```python
SCRAPER_INGEST_SECRET = os.getenv("SCRAPER_INGEST_SECRET")
if SCRAPER_INGEST_SECRET is None or SCRAPER_INGEST_SECRET == "":
    logger.warning("SCRAPER_INGEST_SECRET not set; /ingest endpoint is disabled")

# Middleware — exempt /ingest from the general scraper secret check
@app.middleware("http")
async def check_custom_header(request: Request, call_next):
    if request.url.path in ["/health", "/status"] or request.url.path.startswith("/ingest"):
        response = await call_next(request)
        return response
    # ... existing X-Homekeepr-Scraper check ...

# Endpoint — check ingest-specific secret
@app.post("/ingest/{brand}/{model:path}")
async def ingest_manual_upload(brand: str, model: str, request: Request, file: UploadFile):
    if not SCRAPER_INGEST_SECRET:
        raise HTTPException(status_code=404, detail="Not found")
    if request.headers.get("X-Homekeepr-Ingest") != SCRAPER_INGEST_SECRET:
        raise HTTPException(status_code=401, detail="Unauthorized")
    ...
```

**Secret management:**

- **secrets-manager** (Cloudflare Worker): Add `SCRAPER_INGEST_SECRET` via `wrangler secret put SCRAPER_INGEST_SECRET --env production`. Grant the temporal-jobs machine access via `npx tsx admin.ts add-secret "prod-vps-01" "SCRAPER_INGEST_SECRET" --env production`.
- **temporal-jobs API**: Fetches `SCRAPER_INGEST_SECRET` from secrets-manager at startup (add to `Config` interface and `fetchSecrets()` in `config.ts`). Never on disk.
- **documentation-scraper**: Reads `SCRAPER_INGEST_SECRET` from `.env` on disk — same as `SCRAPER_SECRET` works today. The scraper is a Python app and doesn't have a secrets-manager client. Porting one for a single secret is overkill, but worth doing if the scraper accumulates more secrets later.

The temporal-jobs admin API sends this header when proxying uploads to the scraper. The scraper is still internet-facing on `api.homekeepr.co`, but the `/ingest` endpoint is useless without the ingest secret — and that secret is only shared between two services on the same VPS.

### Security hardening

**A03 — Path traversal in file storage:**

`paths_for()` builds a filesystem path from brand + model: `BLOB_ROOT / category / brand / model / doc_type`. Python's `pathlib` `/` operator does not sanitize `..`. If brand or model contains `../../`, files get written outside `BLOB_ROOT`.

Mitigation: sanitize both brand and model to an allowlist of safe characters, then verify the resolved path is still under `BLOB_ROOT`.

```python
import re

SAFE_PATH_SEGMENT = re.compile(r'^[a-zA-Z0-9_.\-]+$')

def sanitize_path_segment(value: str) -> str:
    """Strip anything that isn't alphanumeric, underscore, hyphen, or dot."""
    sanitized = re.sub(r'[^a-zA-Z0-9_.\-]', '_', value)
    # Collapse runs of underscores and strip leading dots/dashes
    sanitized = re.sub(r'_+', '_', sanitized).strip('_.-')
    if not sanitized:
        raise HTTPException(status_code=400, detail="Invalid brand or model")
    return sanitized

# In the endpoint handler, before calling ingest:
brand = sanitize_path_segment(brand.lower())
normalized_model = sanitize_path_segment(normalize_model(model))

# After paths_for() returns, verify the resolved path:
pdf_path, text_path = paths_for(brand, normalized_model, "owner", sha, "appliance")
if not pdf_path.resolve().is_relative_to(BLOB_ROOT.resolve()):
    raise HTTPException(status_code=400, detail="Invalid path")
```

**A04 — No file size limit:**

Without a limit, an attacker with the ingest secret could exhaust disk space with arbitrarily large uploads.

Mitigation: reject uploads larger than 50MB (larger than any appliance manual). Check `Content-Length` header upfront, and enforce during read as a safety net.

```python
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB

@app.post("/ingest/{brand}/{model:path}")
async def ingest_manual_upload(brand: str, model: str, request: Request, file: UploadFile):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 50MB)")

    # Also enforce during read in case Content-Length is missing/spoofed
    contents = await file.read(MAX_UPLOAD_SIZE + 1)
    if len(contents) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 50MB)")
```

### Error cases

| Scenario | Response |
|----------|----------|
| Missing file | 400 `"file is required"` |
| File is not a valid PDF | 400 `"Invalid PDF file"` |
| File exceeds 50MB | 413 `"File too large (max 50MB)"` |
| Brand or model contains invalid characters | 400 `"Invalid brand or model"` |
| Document already exists for brand/model | 200 with existing document metadata (idempotent) |
| SQLite write fails | 500 with error message |

---

## Files to change

| File | Change |
|------|--------|
| `app/main.py` | Add `POST /ingest/{brand}/{model:path}` endpoint |

One file, one endpoint. All ingestion logic (`validate_and_ingest_manual`, `ingest_from_local_path`, `paths_for`, `insert_or_ignore_document`) is already implemented and reused as-is.

---

## Verification

1. **Upload a real PDF** — `curl -X POST` with a known appliance manual. Verify it appears in the SQLite database and blob storage.
2. **Idempotent re-upload** — upload the same file again. Verify it returns the existing document, not a duplicate.
3. **Invalid file rejection** — upload a non-PDF file (e.g. a text file). Verify 400 response.
4. **Cache hit on scrape** — after uploading, call `GET /scrape/{brand}/{model}`. Verify it returns the uploaded PDF immediately without web scraping.
5. **Auth** — call without `X-Homekeepr-Ingest` header. Verify 401.
6. **Path traversal rejection** — upload with brand `../../etc` or model `../../../tmp/evil`. Verify 400.
7. **Size limit** — upload a file larger than 50MB. Verify 413.
