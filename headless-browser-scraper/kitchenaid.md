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

2. **Headless Browser Initialization**: Launch `undetected-chromedriver` in headless mode with stealth options to avoid bot detection.

3. **Page Fetch**: Navigate to the owners page and wait for the page to load fully.

4. **Open Search Drawer**: Click on the conversion drawer tab to open the search interface.

5. **Enter Model Number**: Click on the input field and type the model number.

6. **Select Model**: Click on the link matching the model number.

7. **Navigate to Manual Page**: Click on the element that opens the manual page in a new window and switch to it.

8. **PDF Link Extraction**: Check if the new page is a direct PDF URL. If so, use it directly. Otherwise, on the manual page, find all `<a>` tags with an `href` ending in `.pdf`. Extract the title from the link text or URL and determine the `doc_type` based on keywords (e.g., "install" → "installation", "service" → "service", else "owner").

9. **Data Collection**: For each PDF found, collect the following metadata:
    *   `brand`: "kitchenaid"
    *   `model_number`: The model number provided.
    *   `doc_type`: The type inferred from the title.
    *   `title`: The text of the PDF link.
    *   `source_url`: The URL of the page where the PDF was found.
    *   `file_url`: The absolute URL of the PDF file.

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