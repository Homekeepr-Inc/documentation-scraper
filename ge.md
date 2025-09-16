# GE Appliance Parts Scraper

This scraper extracts owner's manuals from geapplianceparts.com for specific model numbers.

## URL Pattern
`https://www.geapplianceparts.com/store/parts/assembly/{MODEL}`

Replace {MODEL} with the appliance model number (e.g., CFE28TSHFSS).

## PDF Extraction
Use CSS selector: `a[href$=".pdf"]`

The link text contains the document type (e.g., "Owner's Manual").

## Example HTML Element
```html
<a href="https://products-salsify.geappliances.com/image/upload/s--9rm2e80j--/e8ad6a9b94d6e43a8f81d4cba571f1d4ede839ec.pdf" target="_blank" onclick="window.dataLayer.push({'event': 'download-click','pdfFriendlyName': 'Owner’s Manual'});">Owner’s Manual</a>
```

## Step-by-Step Scraping Process

1.  **URL Construction**: Build the initial URL using the pattern `https://www.geapplianceparts.com/store/parts/assembly/{MODEL}`.

2.  **Headless Browser Initialization**: Launch `undetected-chromedriver` in headless mode with stealth options to avoid bot detection.

3.  **Page Fetch**: Navigate to the constructed URL and wait for the page to load fully.

4.  **Error Page Check**: Parse the page source with BeautifulSoup. Look for an `<h1>` element containing "Uh-oh! There's A Problem" to detect if the model page doesn't exist.

5.  **Keyword Search (Fallback)**: If an error page is detected, construct a search URL like `https://www.geapplianceparts.com/store/parts/KeywordSearch?q={MODEL}` and navigate to it.

6.  **Model Link Extraction**: On the search results page, find an `<a>` tag whose text exactly matches the model number (using a case-insensitive regex like `^{MODEL}$`).

7.  **Specific Model Navigation**: If a matching link is found, extract its `href` attribute, construct the full URL, and navigate to it.

8.  **PDF Link Extraction**: On the final model page, find all `<a>` tags with an `href` ending in `.pdf`. Extract the title from the link text and determine the `doc_type` based on keywords (e.g., "install" → "installation", "service" → "service", else "owner").

9.  **Data Collection**: For each PDF found, collect the following metadata:
    *   `brand`: "ge"
    *   `model_number`: The model number provided.
    *   `doc_type`: The type inferred from the title.
    *   `title`: The text of the PDF link.
    *   `source_url`: The URL of the page where the PDF was found.
    *   `file_url`: The absolute URL of the PDF file.

10. **Ingestion**: Pass the collected data to the ingestion function, which checks for duplicates by `file_url` and SHA256 hash before storing the document and its metadata.

## Implementations

### 1. Scrapy Spider (Blocked by Site)
The scraper is implemented in `crawler/crawler/spiders/ge_spider.py`.

To run:
```bash
cd crawler
python3 -m scrapy crawl ge -a models=CFE28TSHFSS
```

Note: The site blocks automated requests (403 error), making this implementation less reliable.

### 2. Headless Browser Scraper (Stealthy)
For sites that detect bots, use the headless browser scraper in `headless-browser-scraper/ge_headless_scraper.py`.

This uses `undetected-chromedriver` for stealthy scraping.

To run:
```bash
# Via CLI
python3 scripts/cli.py headless-ge CFE28TSHFSS

# Or directly
python3 headless-browser-scraper/ge_headless_scraper.py CFE28TSHFSS
```

It will fetch the page, extract the PDF, and ingest it into the database.
