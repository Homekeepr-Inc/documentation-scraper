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
   - Keep URLs ending in `.pdf` or flagged as PDF in `mime`.
   - Score results using heuristics: presence of model number, doc_type keywords (`owner`, `tech sheet`, `installation`), domain allowlist.
   - Drop duplicates by URL and canonical file name.
6. **Validation Fetch**:
   - Stream download highest-ranked PDF to temp directory.
   - Validate file type, ensure model_number appears in text (re-use `validate_and_ingest_manual`).
   - If validation fails, move to next candidate; log failure reason (mismatch, corrupt, access denied).
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
- Heuristics tuned per brand:
  - Domain allowlist (e.g., `whirlpool.com`, `assets.brand.com`).
  - Keyword boosts (owner, manual, guide, spec sheet) and penalties (marketing, rebate).
  - Model number exact match vs. fuzzy (tokenized uppercase comparison).
- Expose score thresholds via config so ops can adjust without redeploy.

### PDF Fetcher & Validator
- Streams downloads with timeout guard (e.g., 15s) and size ceiling (reject > 25 MB unless brand override).
- Reuses shared validation pipeline to ensure consistent ingestion.
- Stores raw PDF alongside metadata to enable dedupe and caching.

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
- Config file (YAML/JSON) for per-brand templates, allowlists, scoring weights, rate limit settings.
- Feature flag (`SERPAPI_ENABLED`) to toggle new flow per brand during rollout.

## Monitoring & Alerting
- Metrics: queries per brand, success/failure counts, average score of accepted PDFs, validation failure reasons, fallback invocations.
- Logs: structured entries with `brand`, `model_number`, `search_id`, `selected_url`.
- Alerts:
  - High failure rate per brand (>30% over 1h).
  - SerpApi quota nearing threshold.
  - Download validation failures due to HTML pages masquerading as PDFs.

## Cost & Rate Limit Management
- SerpApi free tier exhausted quickly; maintain rolling cost estimation per brand.
- Batch low-priority requests via queue to smooth peaks.
- Implement adaptive throttling: if near daily quota, downgrade to headless scrapers or queue jobs for next window.

## Rollout Plan
1. Instrumentation groundwork: add SerpApi client with dry-run mode logging candidate results only.
2. Pilot for Whirlpool models already supported; compare manual overlap and ingestion success vs. headless baseline.
3. Expand to Sub-Zero and Frigidaire with minimal fallback, validate coverage.
4. Integrate fallback routing and health switching for partially indexed brands.
5. Deprecate redundant Selenium flows where SerpApi yields 95%+ success over 30-day window.

## Risks & Mitigations
- **Incomplete Coverage**: Some domains unindexed; mitigate via health monitors and fallback library.
- **Result Drift**: Google ranking changes; keep scoring heuristics tunable and monitor manual mismatch alerts.
- **Quota Exhaustion**: Implement throttling and budget guardrails; maintain headless scrapers as reserve.
- **False Positives**: Validate model occurrence and leverage DQA pipeline prior to user exposure.

## Open Questions
- Do we want to persist the full SerpApi result set for auditing or only top-N?
- Should we expand beyond PDFs (HTML manuals) and convert them, or leave as future work?
- How do we prioritize doc types (owner vs. tech sheet) when multiple results exist and the request is ambiguous?
- What SLA do we expect from SerpApi, and do we need multi-provider fallback (e.g., RapidAPI Google search)?
