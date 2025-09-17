# Whirlpool Appliance Scraper

This scraper extracts owner's manuals from whirlpool.com for specific model numbers.

## URL Pattern
`https://www.whirlpool.com/results.html?term=<model number here>`

Replace `<model number here>` with the appliance model number (e.g., WRT311FZDW).

## PDF Extraction
The target element is an `<a>` tag with the class `clp-item-link` and the text "Owner's Manual".

## Example HTML Element
```html
<a href="/content/dam/global/documents/202102/owners-manual-w11436596-reva.pdf" class="clp-item-link" target="_blank">Owner's Manual</a>
```

## Step-by-Step Scraping Process

1.  **URL Construction**: Build the search URL using the pattern `https://www.whirlpool.com/results.html?term=<model_number>`.
2.  **Headless Browser Initialization**: Launch `undetected-chromedriver` in headless mode.
3.  **Page Fetch**: Navigate to the constructed URL and wait for the page to load.
4.  **Link Extraction**: Find the `<a>` tag with the class `clp-item-link` and the text "Owner's Manual".
5.  **URL Construction**: Extract the `href` attribute and join it with `https://www.whirlpool.com/` to create the full PDF URL.
6.  **Ingestion**: Pass the collected data to the `ingest_from_url` function to download the PDF and store its metadata.

## How to Run

```bash
python3 headless-browser-scraper/whirlpool_headless_scraper.py WRT311FZDW
```
