## Overview of Headless Scrapers
Basic API calls and html parsing usually don't work anymore. The services it _does_ work on are often not granular enough to confidently and reliably find the requested document.

We can use headless browser scrapers to avoid basic bot prevention techniques by manufacturer websites.

Most providers, as of Sep 2025, do not heavily fingerprint the browser to a level where we are getting booted or banned.

Over time, our risk of getting IP / fingerprint banned will be lower as we amass more manuals i.e we've already crawled the request model number before; and thus can serve the file from disk.

## How it works
We use Selenium to orchestrate the browser to download PDFs for various manufacturers.

We use a global queue based system to handle workloads across all scrapers. Currently, we use a parallelism of 2, allowing up to 2 browser instances to load concurrently, regardless of brand.

This prevents resource exhaustion when multiple requests arrive for different brands. Monitor resource usage and adjust the semaphore value in parallelism.py if needed.

The API provides a single consolidated endpoint `/scrape/{brand}/{model}` that handles all supported brands (GE, LG, Kitchenaid, Whirlpool). Requests are enqueued globally and processed asynchronously.

Again, as time goes on and we amass more manuals, the calls requiring us to actually scrape will become less and less frequent.

We also don't have hard time requirements. Faster is better, but its okay if it takes ~20 seconds to fetch a manual. Our RAG pipeline takes longer.

## Architecture
- `parallelism.py`: Manages global job queue and semaphore for controlling concurrent browser instances across all scrapers.
- Individual scraper modules (e.g., `lg_scraper.py`, `ge_headless_scraper.py`) contain brand-specific scraping logic.
- API endpoints in `app/main.py` enqueue jobs via `parallelism.py` instead of direct scraping.

## Temp Directory Management
To prevent race conditions between concurrent scraping jobs, each scraper uses isolated per-job temp directories:

- **Per-Job Isolation**: Each scraping job creates its own temp directory under `headless-browser-scraper/temp/` using `create_temp_download_dir()`
- **Download Process**: PDFs are downloaded to the job's temp directory, validated, then moved to permanent storage via `ingest_from_local_path()`
- **Cleanup Timing**: Temp directories are cleaned up at the API level in `app/main.py` after successful ingestion using `cleanup_temp_dir()`
- **Path Validation**: Uses `os.path.commonpath()` to ensure only temp directories within the expected base path are cleaned up
- **Race Condition Prevention**: Eliminates conflicts when multiple jobs download PDFs with similar filenames simultaneously

This approach ensures reliable cleanup while preventing premature deletion of files still being processed by other jobs.

## Conventions to Follow (Important!)
To ensure timeliness and robustness, we have a few utility functions which should be used in certain circumstances:
- Never using `print()` calls in loops as they can slow down execution by _many_ orders of magnitude. Progress `print()` calls are fine.
- `safe_driver_get`: like driver.get in Selenium, but adds a 10s timeout to avoid stopping the world and blocking the queue.
  - **Always use this instead of driver.get to avoid blocking the queue!**
- `wait_for_download`: polls the disk to ensure a file is fully downloaded before continuing i.e attempting to ingest file into sqlite via `ingest_manual`.
  - **Always use this instead of implementing something else yourself!**
- `duckduckgo_fallback`: if all scraper attempts fail, we have one final escape hatch to try and find the correct product page containing the desired manual. Note that this is a generic search for a particular model number, and is manufacturer-agnostic on purpose. Because of this, a brand-specific fallback function must be passed into `duckduckgo_fallback` to run if the duckduckgo fallback succeeds to find a page we support scraping for.
- **PDF Validation and Ingestion**: Always use `validate_and_ingest_manual()` instead of `ingest_manual()` for consistent validation. This function:
  - Validates the PDF file format
  - Validates that the PDF content contains the model number (to prevent downloading wrong manuals)
  - Handles both local files and URLs
  - **Always use this for final ingestion in ALL scrapers!**
- **Model Normalization for Caching**: When scraping models that may contain special characters (e.g., `/AA` in Samsung models), ensure the `model_number` in the returned dictionary is consistently normalized (e.g., replace `/` with `_`). The API lookup uses this normalized value, so mismatches will prevent caching. Always use the same normalization logic in both primary and fallback scrapers to avoid this recurring issue.
- **Caching Failure Conditions**: Caching won't work if:
  - (1) No prior scrape exists
  - (2) Model normalization mismatches
  - (3) Ingestion fails or `local_path` is invalid/missing
  - (4) Brand doesn't match
  - (5) Scraper returns `None`
  - (6) DB/query errors occur. Debug by checking DB for matching `brand`, `model_number`, and valid `local_path`.