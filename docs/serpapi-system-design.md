# SerpApi Scraper System Design

## Background
- Current PDF acquisition pipeline relies on Selenium-driven VPS scrapers that recreate end-user clicks and downloads per brand.
- Flow is brittle: per-site DOM assumptions, sequencing of clicks, and throttled browser automation lead to high maintenance overhead and slow turnaround.
- Early experiments with SerpApi show that a single Google query returns a complete set of Whirlpool manuals (owner's, spec sheet, tech sheet, etc.) without bespoke navigation.

## Goals
- Make SerpApi the first-line retrieval path for every brand before invoking legacy automations.
- Minimize orchestration steps required to obtain high-quality manuals for any brand/model.
- Centralize search, ranking, and ingestion logic so downstream RAG ingestion receives clean, deduplicated PDFs.
- Preserve ability to fall back to existing headless scrapers for brands or domains that are not indexed.

## Non-Goals
- Replacing the ingestion, chunking, or embedding pipeline (those stages remain unchanged).
- Building a general-purpose Google Search proxy; we only cover manual retrieval and related appliance documentation.

## Functional Requirements
- Accept `{brand, model_number}` requests from existing `/scrape/{brand}/{model}` API.
- Construct deterministic search queries (e.g., `"Whirlpool WFW5620HW owner's manual filetype:pdf site:whirlpool.com"`).
- Call SerpApi, filter for PDF results, and rank the candidate manuals.
- Download selected PDFs, validate against requested model, and persist to storage (Supabase + blob store).
- Emit metadata required by ingestion pipeline: `brand`, canonicalized `model_number`, `doc_type`, `title`, `source_url`, `file_url`, checksum, byte size.
- Provide automated fallbacks when SerpApi misses a brand: domain-targeted headless scraper, cached manual, or manual review queue.

## Non-Functional Requirements
- Target < 5s median time-to-first-PDF per manual (bypasses headless browser boot).
- Respect SerpApi rate limits and budget caps (monitor QPS and cost).
- Observable: metrics for query volume, result quality score, download success, ingestion success.
- Resilient to network blips and partial SerpApi outages (retry with jitter, degrade gracefully).
- Configurable query templates per brand and per doc_type without redeploying code.

## High-Level Architecture
```
┌────────────────┐     ┌───────────────────┐     ┌─────────────────┐
│ Scrape Request │───▶ │ Query Orchestrator│───▶ │  SerpApi Client  │
└────────────────┘     └───────────────────┘     └────────┬────────┘
                                                             │
                                                             ▼
                                         ┌────────────────────────────┐
                                         │ Result Scorer & Filter     │
                                         └────────────┬───────────────┘
                                                      │
                                         ┌────────────▼────────────┐
                                         │ PDF Fetcher & Validator │
                                         └────────────┬────────────┘
                                                      │
                                        ┌─────────────▼─────────────┐
                                        │ Ingestion & Quality Checks│
                                        └─────────────┬─────────────┘
                                                      │
                                   ┌──────────────────▼──────────────────┐
                                   │ Supabase + Document Embedding Stack │
                                   └──────────────────────────────────────┘
```

## End-to-End Flow
1. **Request Intake**: API receives `{brand, model_number}`, normalizes model (e.g., replace `/` with `_`).
2. **Cache Lookup**: Check Supabase/document store for existing validated manual; return immediately if present.
3. **Query Construction**: Build brand-specific query string(s). Allow multiple variants (owner's manual, installation guide) per invocation based on user intent.
4. **SerpApi Call**: Call `/search.json` with API key, location (default Austin), `engine=google`, and query. Log `search_metadata.id` for traceability. SerpApi always runs before any headless scraper regardless of brand.
5. **Result Filtering**:
   - Keep only candidates whose URL looks like a PDF (strip query params and require a `.pdf` suffix); drop everything else immediately.
   - Score each candidate deterministically: +40/+30/+20 for model matches in URL/title/snippet, +20 for domain allowlist hit, +25/+15/+10 depending on inferred doc_type (`owner`/`installation`/`tech`), and a small boost for higher SERP positions.
   - Seed `doc_type` inference from title + URL keywords (owner, installation, tech, spec, guide) and carry the score along with query metadata.
   - Deduplicate by exact URL before download, then sort by score and attempt the top five results per query.
6. **Validation Fetch**:
   - Stream download the highest-ranked remaining candidate into a temp directory.
   - Run `evaluate_pdf_candidate`, which inspects up to the first six pages (20k chars) with `pypdf` to compute `pdf_features` (keyword hits per doc type, marketing signals, manual token count, model presence, page count).
   - Reject early if heuristics fail: owner manuals shorter than four pages, marketing-weighted PDFs, absence of owner keywords, or failed text extraction unless the fallback image-manual rules apply.
   - Persist structured `pdf_features` + rejection reason in logs/metadata; on failure clean up and try the next candidate.
7. **Ingestion & Quality Checks (Done in Supabase)**:
   - On success, move file to blob storage, compute checksum, capture metadata.
   - Emit job record to ingestion queue for text extraction, chunking, embedding.
   - Tag manual with `source=serpapi` for provenance.
8. **Fallback Handling**:
   - If all candidates fail to validate (no high-quality SerpApi PDF), dispatch to the existing brand-specific headless scraper with minimal steps (direct product page fetch).
   - If fallback fails, push to manual review queue and surface user-facing “manual pending” status.

## Component Details
### Query Orchestrator
- Config-driven mapping: `{brand: {primary_query_template, secondary_templates[]}}`.
- Supports future expansion to doc_type-specific templates (installation, tech sheet, quick start).
- Allows experimentation with additional filters (e.g., `intitle` or `site` overrides) per brand without code changes.

### SerpApi Client
- Thin wrapper around SerpApi REST; handles authentication, retries (exponential with max 3 attempts), and rate-limit backoff (respect `HTTP 429`).
- Capture `search_metadata` and `organic_results` snapshot for debugging (store lightweight JSON in observability bucket).

### Result Scorer & Filter
- Deterministic score built from SerpApi payload:
  - +40/+30/+20 for model matches in URL/title/snippet (case-insensitive).
  - +20 when the candidate domain matches the brand allowlist.
  - +25/+15/+10 based on inferred doc_type (`owner`, `installation`, `tech` respectively) determined from title/URL keywords; default to `owner` when unknown.
  - + (12 - SERP position) to slightly reward higher-ranked organic results.
- Doc type inference seeds downstream validation; only `owner`, `installation`, and `tech` candidates move forward after PDF analysis.
- Duplicates (same URL) are skipped; orchestrator keeps a `seen_urls` set across all result buckets before sorting by score.
- Only the top five scored candidates per query are attempted to control download cost.

### PDF Fetcher & Validator
- Streams downloads with timeout guard (e.g., 15s) and size ceiling (reject > 25 MB unless brand override).
- Performs lightweight MIME/content-type verification before persisting to disk.
- Analyzes the first six pages (max 20k characters) via `pypdf` to populate `pdf_features`:
  - Keyword hit counts per doc type (`owner`, `installation`, `tech`, `guide`), marketing keyword counts, manual token counts, model-number presence, text extraction success, page count.
  - Flags `too_short_for_owner` when page_count < 4 so two-page brochures cannot be accepted as owner manuals.
  - Sets `fallback_image_manual` only when text is absent but the document is long enough (≥5 pages) to plausibly be a scan.
- Rejects candidates that fail heuristics: disallowed doc_type, no manual keywords, marketing-heavy with no owner signal, short owner manuals, or invalid PDFs.
- Provides structured log entries (`serpapi.orchestrator`) for every decision, including `pdf_analysis_reason`, and attaches `pdf_features` to the ingestion metadata for downstream auditing.
- Cleans up temp directories on every failure to avoid orphan files; only accepted manuals flow into ingestion.

### Ingestion & Data Quality
- After validation, enqueue manual for existing LLM extraction pipeline (text extraction, chunking, embedding).
- Enrich metadata with confidence score (`serpapi_score`, `validation_checks_passed`).
- Persist ingestion outcomes so we can track precision/recall of SerpApi strategy.

## Fallback Strategy
- Maintain brand capability matrix:
- All brands enqueue via SerpApi first; tiers define which fallback executes automatically if SerpApi yields no validated PDFs:
  - **Tier 1**: Fully indexed brands (Whirlpool, Sub-Zero, Frigidaire) – fallback rarely triggered, but legacy scraper remains available.
  - **Tier 2**: Partially indexed (ElectroluxMedia) – SerpApi first, then targeted headless page fetch.
  - **Tier 3**: Not indexed / blocked – SerpApi still attempted to catch edge cases; legacy headless script expected to run immediately after failure.
- Implement guardrail: if SerpApi returns < N PDFs for a brand over rolling window, trigger health alert and auto-switch to headless mode.

## Configuration & Secrets
- Store SerpApi key in existing secret manager (`SERPAPI_KEY`).
- Per-brand query templates, allowlists, and candidate caps live in `serpapi_scraper/config.py` (dataclass constants checked into the repo today); long term we can externalize this to YAML/JSON if ops needs runtime edits.
- Feature flag (`SERPAPI_ENABLED`) to toggle new flow per brand during rollout.

## Monitoring & Alerting
- Metrics: queries per brand, success/failure counts, average score of accepted PDFs, validation failure reasons, fallback invocations.
- Logs: structured entries emitted by `serpapi.client` (request lifecycle), `serpapi.orchestrator` (candidate scoring, PDF analysis, rejection reasons), and `ingest` (downstream ingestion) with `brand`, `model`, `search_id`, `candidate_url`, `pdf_analysis_reason`.
- Alerts:
  - High failure rate per brand (>30% over 1h).
  - SerpApi quota nearing threshold.
  - Download validation failures due to HTML pages masquerading as PDFs.

## Cost & Rate Limit Management 
- SerpApi free tier exhausted quickly; maintain rolling cost estimation per brand.
- Batch low-priority requests via queue to smooth peaks.
- Implement adaptive throttling: if near daily quota, downgrade to headless scrapers or queue jobs for next window.

## Risks & Mitigations
- **Incomplete Coverage**: Some domains unindexed; mitigate via health monitors and fallback library.
- **Result Drift**: Google ranking changes; keep scoring heuristics tunable and monitor manual mismatch alerts.
- **Quota Exhaustion**: Implement throttling and budget guardrails; maintain headless scrapers as reserve.
- **False Positives**: Validate model occurrence and leverage DQA pipeline prior to user exposure (to be handled by data pipeline (yet to be built))

## Open Questions
- Do we want to persist the full SerpApi result set for auditing or only top-N?
- Should we expand beyond PDFs (HTML manuals) and convert them, or leave as future work?
- How do we prioritize doc types (owner vs. tech sheet) when multiple results exist and the request is ambiguous?
