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

curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/lg/WM4000HWA' &
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/lg/WT7300CW' &
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/lg/WKEX200HBA' &
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/lg/WM9500HKA' &
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/lg/WM6700HBA' &
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/lg/WT7900HBA' &
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/lg/WM4500HBA'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/lg/WT7400CV'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/lg/WM8900HBA'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/lg/WM3400CW'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/lg/WM3600HWA'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/lg/WM4200HWA'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/lg/WT7150CW'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/lg/WM3700HVA'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/lg/DLEX4000W'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/lg/DLGX4001B'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/lg/DLEX4200W'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/lg/DLGX4201B'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/lg/WKE100HVA'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/lg/DLEX6700B'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/lg/DLG7401WE'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/lg/DLEX4500B'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/lg/DLGX8901B'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/lg/DLEX7900WE'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/lg/DLG3401W'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/lg/DLEX3700W'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/lg/DLHC1455W'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/lg/DLEX3900W'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/lg/DLG7301WE'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/lg/LFXS26973S'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/lg/LRFVC2406S'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/lg/LRMVS3006S'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/lg/LRSXS2706V'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/lg/LMXS28626S'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/lg/LFXC22526S'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/lg/LRSOS2706S'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/lg/LFCS27596S'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/lg/LTCS24223S'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/lg/LRYKS3106S'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/lg/LRFDS3016S'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/lg/LMWC23626S'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/lg/LSXC22396S'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/lg/LRMVC2306S'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/lg/LFDS22520S'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/lg/LUFNS1131V'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/lg/LUPXC2386N'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/lg/LRTNC1131V'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/lg/LNS1131V'
