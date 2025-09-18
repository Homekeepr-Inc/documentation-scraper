## Overview of Headless Scrapers
Basic API calls and html parsing usually don't work anymore. The services it _does_ work on are often not granular enough to confidently and reliably find the requested document.

We can use headless browser scrapers to avoid basic bot prevention techniques by manufacturer websites.

Most providers, as of Sep 2025, do not heavily fingerprint the browser to a level where we are getting booted or banned.

Over time, our risk of getting IP / fingerprint banned will be lower as we amass more manuals i.e we've already crawled the request model number before; and thus can serve the file from disk.

## How it works
We use Selenium to orchestrate the browser to download PDFs for various manufacturers. 

We use a queue based system to handle workloads. Currently, we use a parallelism of 1, so only once browser instance loads at a time.

This is mainly due to RAM constraints. We likely won't need to scale this VPS beyond 2 cores and some extra RAM, if any.

Again, as time goes on and we amass more manuals, the calls requiring us to actually scrape will become less and less frequent.

We also don't have hard time requirements. Faster is better, but its okay if it takes ~20 seconds to fetch a manual. Our RAG pipeline takes longer.

## Conventions
To ensure timeliness and robustness, we have a few utility functions which should be used in certain cirumstances:
- `safe_driver_get`: like driver.get in Selenium, but adds a 10s timeout to avoid stopping the world and blocking the queue.
  - **Always use this instead of driver.get to avoid blocking the queue!**
- `wait_for_download`: polls the disk to ensure a file is fully downloaded before continuing i.e attempting to ingest file into sqlite via `ingest_manual`.
- `duckduckgo_fallback`: if all scraper attempts fail, we have one final escape hatch to try and find the correct product page containing the desired manual. Note that this is a generic search for a particular model number, and is manufacturer-agnostic on purpose. Because of this, a brand-specific fallback function must be passed into `duckduckgo_fallback` to run if the duckduckgo fallback succeeds to find a page we support scraping for.