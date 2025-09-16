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

## Implementations

### 1. Scrapy Spider (Blocked by Site)
The scraper is implemented in `crawler/crawler/spiders/ge_spider.py`.

To run:
```bash
cd crawler
python3 -m scrapy crawl ge -a models=CFE28TSHFSS
```

Note: The site blocks automated requests (403 error).

### 2. Headless Browser Scraper (Stealthy)
For sites that detect bots, use the headless browser scraper in `headless-browser-scraper/ge_headless_scraper.py`.

This uses undetected-chromedriver for stealthy scraping.

To run:
```bash
# Via CLI
python3 scripts/cli.py headless-ge CFE28TSHFSS

# Or directly
cd headless-browser-scraper
python3 ge_headless_scraper.py CFE28TSHFSS
```

It will fetch the page, extract the PDF, and optionally download it.

## Model Filtering
Pass multiple models as comma-separated for Scrapy: `-a models=MODEL1,MODEL2`

For headless scraper, run separately per model.

## Output
Yields items with:
- brand: "ge"
- model_number: extracted or provided
- doc_type: inferred from title/URL
- title: link text
- source_url: page URL
- file_url: PDF URL