# LG Appliance Manuals Scraper

This scraper extracts owner's manuals from lg.com for specific model numbers.

## URL Pattern
`https://www.lg.com/us/support/product/{model}`

Replace {model} with the appliance model number (e.g., LMXS28626S). If the page shows an error, retry with `lg-{model}`.

## PDF Extraction
For standard pages: Find `<div class="manualList">` then `<div class="c-resources__item--download-button">` containing an `<a>` with the PDF href.

For lg- prefixed pages: Use recorded Selenium actions to navigate tabs, click elements, and extract or download the PDF.

Fallback: If scraping fails, perform a DuckDuckGo search for the model on lg.com/us and scrape from the resulting LG page.

## Example HTML Elements
### Standard Page
```html
<div class="manualList">
  <div class="c-resources__item--download-button">
    <a href="https://gscs-b2c.lge.com/downloadFile?fileId=..." target="_blank">...</a>
  </div>
</div>
```

### lg- Prefixed Page
Complex structure with tabs and download buttons, accessed via CSS selectors like `#simple-tab-1 > .MuiTypography-root`.

## Step-by-Step Scraping Process

1. **URL Construction**: Build the initial URL as `https://www.lg.com/us/support/product/{model}`.

2. **Headless Browser Initialization**: Launch `undetected-chromedriver` in headless mode with stealth options and download preferences.

3. **Page Fetch**: Navigate to the URL and wait for JS rendering.

4. **Error Handling**: Check for "guide-error" or 404 indicators. If found, retry with `lg-{model}` prefix and perform additional actions like dismissing consent overlays and scrolling.

5. **PDF Extraction**:
   - For non-lg pages: Parse HTML for `manualList` div and extract PDF href.
   - For lg- pages: Execute recorded actions (click manuals tab, scroll, click download button) to get PDF URL or trigger download.
   - Fallback: Use DuckDuckGo search to find an LG page and scrape from there.

6. **Download and Validation**: Download the PDF (if URL) or use the local downloaded file. Validate by checking if content starts with `%PDF-`.

7. **Data Collection**: Collect metadata:
    * `brand`: "lg"
    * `model_number`: The model number.
    * `doc_type`: "owner" (default).
    * `title`: "Owner's Manual"
    * `source_url`: The page URL.
    * `file_url`: The PDF URL or local path.

8. **Ingestion**: Pass data to ingestion function for duplicate checking and storage.

## Implementations

### Headless Browser Scraper
Uses `headless-browser-scraper/lg_scraper.py` with threading for multiple models.

To run:
```bash
python3 headless-browser-scraper/lg_scraper.py LMXS28626S CFE28TSHFSS
```

It handles one model at a time due to site restrictions, downloads PDFs, and ingests them.

## Example Model Numbers

curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/lg/WM4000HWA &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/lg/WT7300CW &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/lg/WKEX200HBA &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/lg/WM9500HKA &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/lg/WM6700HBA &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/lg/WT7900HBA &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/lg/WM4500HBA &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/lg/WT7400CV &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/lg/WM8900HBA &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/lg/WM3400CW &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/lg/WM3600HWA &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/lg/WM4200HWA &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/lg/WT7150CW &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/lg/WM3700HVA &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/lg/DLEX4000W &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/lg/DLGX4001B &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/lg/DLEX4200W &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/lg/DLGX4201B &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/lg/WKE100HVA &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/lg/DLEX6700B &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/lg/DLG7401WE &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/lg/DLEX4500B &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/lg/DLGX8901B &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/lg/DLEX7900WE &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/lg/DLG3401W &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/lg/DLEX3700W &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/lg/DLHC1455W &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/lg/DLEX3900W &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/lg/DLG7301WE &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/lg/LFXS26973S &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/lg/LRFVC2406S &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/lg/LRMVS3006S &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/lg/LRSXS2706V &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/lg/LMXS28626S &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/lg/LFXC22526S &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/lg/LRSOS2706S &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/lg/LFCS27596S &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/lg/LTCS24223S &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/lg/LRYKS3106S &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/lg/LRFDS3016S &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/lg/LMWC23626S &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/lg/LSXC22396S &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/lg/LRMVC2306S &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/lg/LFDS22520S &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/lg/LUFNS1131V &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/lg/LUPXC2386N &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/lg/LRTNC1131V &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/lg/LNS1131V