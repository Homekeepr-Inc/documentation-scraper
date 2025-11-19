# Adding A New SerpApi Fallback Scraper

This guide explains how to plug an additional “progressive fallback” into `serpapi_scraper/orchestrator.py`. Follow these steps whenever a new data source (site-specific scraper, HTML flow, etc.) should be tried after the primary Manualslib search fails.

## 1. Understand The Existing Flow

1. `fetch_manual_with_serpapi` runs the ordered SerpApi query stages defined in `serpapi_scraper/config.py` (see `SCRAPER_QUERY_STAGES`).
2. If those queries produce *zero candidates*, the orchestrator calls a fallback query provider (default: `default_fallback_query_provider`) to build the next set of search strings.
3. Each query runs through `collect_candidates`, which filters candidate URLs. Supported HTML candidates are determined by `is_allowed_html_candidate`, and their downloads happen inside `attempt_candidate`.

When you add a brand-new fallback, you typically change two areas:

* Introduce scraper-specific helpers (URL detection, HTML parsing, downloader).
* Extend the fallback query provider and candidate handling so the orchestrator can discover and validate the new source.

## 2. Implement The Scraper

Create small, composable helpers close to the orchestrator (see `serpapi_scraper/searspartsdirect_scraper.py` for a concise example).

1. **URL detector** – Add a `is_<site>_manual_page(url: str) -> bool` function that:
   * Verifies the host belongs to the new domain.
   * Ignores direct PDF links (those are already handled by `download_pdf`).
2. **HTML parser** – Use Selenium DOM queries (e.g., CSS/XPath via `WebDriverWait`) to locate the canonical download link.
3. **Downloader** – Use a Selenium flow (via `headless-browser-scraper/utils.py`) to:
   * Load the landing page and interact with any required buttons.
   * Trigger the browser download (direct HTTP downloads from Python are disallowed).
   * Wait for the file with `wait_for_download` and return `(local_path, pdf_url)` so the orchestrator can fill out metadata.

Keep each helper isolated and well-logged; this makes it easier for future contributors to add more fallbacks by copying the pattern.

> **Policy:** Do not issue direct HTTP downloads from Python for these fallbacks. Always drive the site with Selenium and let Chrome handle the final PDF download so we stay consistent with proxying, cookie handling, and audit requirements.

## 3. Register The Candidate

Update `is_allowed_html_candidate` to include the new detector, ensuring SerpApi results referencing your domain are not discarded in `collect_candidates`.

Inside `attempt_candidate`:

1. After the Manualslib block, add a conditional that triggers the new downloader when the candidate URL matches your detector.
2. If download fails, clean up the temp directory and return `None` (this keeps the retry semantics consistent).
3. When download succeeds:
   * Provide `local_path`, `file_url`, and `source_url`.
   * Append any scraper-specific metadata (e.g., product page URL) onto `result["serpapi_metadata"]`.

## 4. Add A Fallback Query

Fallback queries are injected via `fallback_query_provider`, which defaults to `default_fallback_query_provider`. To add a new site:

1. Extend `default_fallback_query_provider` to append your site-specific search string (or create a brand-new provider and pass it via the `fallback_query_provider` argument of `fetch_manual_with_serpapi`).
2. Each string should be a complete SerpApi query, typically using `site:<domain>` plus a phrase like `"owner's manual"`.
3. Order strings to match the progression you want (earliest entries run first).

Example:

```python
def default_fallback_query_provider(config, model):
    queries = []
    subject = f"{config.display_name} {model}".strip()
    queries.append(f"{subject} owner's manual site:searspartsdirect.com")
    queries.append(f"{subject} owner's manual site:newsource.com")
    return queries
```

Remember that fallbacks only run when the primary Manualslib batch produced zero candidates, so multiple fallback strings are safe—they will run sequentially.

## 5. Validate

1. Unit-test any pure helpers (HTML parsing, URL detection).
2. Run `python -m py_compile serpapi_scraper/orchestrator.py` or the project’s lint suite.
3. Execute an end-to-end fetch with a model known to require your fallback domain and confirm:
   * The candidate appears in the logs.
   * `attempt_candidate` downloads and validates the PDF.
   * Metadata records your scraper-specific fields (useful for debugging ingestion issues).

Following this pattern keeps new fallbacks consistent, dependency-injectable, and easy for the next engineer to extend.
