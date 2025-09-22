# Kitchenaid Appliance Manuals Scraper

This scraper extracts owner's manuals from kitchenaid.com for specific model numbers.

## URL Pattern
`https://www.kitchenaid.com/owners.html`

Search for the model number on the owners page.

## PDF Extraction
Use CSS selector: `a[href$=".pdf"]`

The link text contains the document type (e.g., "Owner's Manual").

## Example HTML Element
```html
<a href="https://some-url.pdf" target="_blank">Owner's Manual</a>
```

## Step-by-Step Scraping Process

1. **Initial Navigation**: Navigate to `https://www.kitchenaid.com/owners.html`.

2. **Headless Browser Initialization**: Launch `undetected-chromedriver` in headless mode with stealth options to avoid bot detection, configured for automatic PDF downloads.

3. **Page Fetch**: Navigate to the owners page and wait for the page to load fully.

4. **Open Search Drawer**: Click on the conversion drawer tab to open the search interface.

5. **Enter Model Number**: Click on the input field and type the model number.

6. **Select Model**: Click on the link matching the model number to navigate to the model-specific page.

7. **PDF Extraction on Model Page**: On the model page, find the first `<a>` tag with an `href` ending in `.pdf`. Navigate to the PDF URL, which triggers an automatic download. Wait for the download to complete and rename the file to `{model}.pdf` in the blob directory.

8. **Fallback Mechanism**: If the model link is not found or scraping fails, attempt a direct URL fallback to `https://www.kitchenaid.com/owners-center-pdp.{model}.html` and repeat the PDF extraction process.

9. **Data Collection**: Collect the following metadata:
    *   `brand`: "kitchenaid"
    *   `model_number`: The model number provided.
    *   `doc_type`: "owner" (default, can be refined based on URL keywords like "install" or "service").
    *   `title`: "Owner's Manual" or inferred from URL (e.g., "Installation Manual" if "install" in URL).
    *   `source_url`: The URL of the page where the PDF was found.
    *   `file_url`: The local file path to the downloaded PDF (e.g., `/path/to/blob/{model}.pdf`).

10. **Ingestion**: Pass the collected data to the ingestion function, which checks for duplicates by `file_url` and SHA256 hash before storing the document and its metadata.

## Implementations

### 1. Headless Browser Scraper (Stealthy)
For sites that detect bots, use the headless browser scraper in `headless-browser-scraper/kitchenaid_headless_scraper.py`.

This uses `undetected-chromedriver` for stealthy scraping.

To run:
```bash
# Via CLI
python3 scripts/cli.py headless-kitchenaid KOES530PSS

# Or directly
python3 headless-browser-scraper/kitchenaid_headless_scraper.py KOES530PSS
```

It will fetch the page, extract the PDF, and ingest it into the database.


## Example Model Numbers
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/kitchenaid/KRFC704FSS &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/kitchenaid/KRSF705HPS &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/kitchenaid/KRFF507HPS &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/kitchenaid/KRSC703HPS &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/kitchenaid/KBFN502EBS &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/kitchenaid/KDTM604KPS &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/kitchenaid/KDPM604KPS &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/kitchenaid/KDFE104HPS &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/kitchenaid/KDTM404KPS &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/kitchenaid/KDPM804KPS &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/kitchenaid/KSGG700ESS &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/kitchenaid/KFID500ESS &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/kitchenaid/KFGG500ESS &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/kitchenaid/KSEG700ESS &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/kitchenaid/KSDG950ESS &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/kitchenaid/KODE500ESS &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/kitchenaid/KOSE500ESS &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/kitchenaid/KODC704FSS &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/kitchenaid/KODE900HSS &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/kitchenaid/KOCE500ESS &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/kitchenaid/KCGS550ESS &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/kitchenaid/KICU509XBL &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/kitchenaid/KCES550HBL &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/kitchenaid/KCGS950ESS &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/kitchenaid/KCES956HSS