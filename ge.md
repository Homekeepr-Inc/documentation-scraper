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

## Implementation
The scraper is implemented in `crawler/crawler/spiders/ge_spider.py`.

To run:
```bash
cd crawler
python3 -m scrapy crawl ge -a models=CFE28TSHFSS
```

Note: The site may block automated requests (403 error). If so, access the URL in a browser, copy the page HTML, and provide it for local parsing.

## Model Filtering
Pass multiple models as comma-separated: `-a models=MODEL1,MODEL2`

## Output
Yields items with:
- brand: "ge"
- model_number: extracted or provided
- doc_type: inferred from title/URL
- title: link text
- source_url: page URL
- file_url: PDF URL