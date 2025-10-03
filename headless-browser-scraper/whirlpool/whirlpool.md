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

1.  **URL Construction**: Build the search URL using the pattern `https://www.whirlpool.com/results.html?term={model_number}`.

2.  **Headless Browser Initialization**: Launch `undetected-chromedriver` in headless mode with download preferences.

3.  **Page Fetch**: Navigate to the search URL and wait for the page to load.

4.  **Link Extraction**: Find the `<a>` tag with class `clp-item-link` and text "Owner's Manual". Extract the href and navigate to it, triggering PDF download. Wait for download, rename to `{model}.pdf`.

5.  **Fallback Mechanism**: If "Owner's Manual" link not found on search page, try direct URL `https://www.whirlpool.com/owners-center-pdp.{model}.html`. On this page, find the div with `data-doc-type="owners-manual"` and click the nested `<a>` to download the PDF.

6.  **Data Collection**: Collect metadata:
    * `brand`: "whirlpool"
    * `model_number`: The model number.
    * `doc_type`: "owner"
    * `title`: "Owner's Manual"
    * `source_url`: The page URL.
    * `file_url`: Local path to downloaded PDF (e.g., `/path/to/blob/{model}.pdf`).

7.  **Ingestion**: Pass data to ingestion function for duplicate checking by file_url and SHA256 hash, then store document and metadata.

## How to Run

```bash
python3 headless-browser-scraper/whirlpool_headless_scraper.py WRT311FZDW
```

It downloads the PDF locally and ingests it into the database.

## Example Model Numbers
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/whirlpool/WRX735SDHZ'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/whirlpool/WFW5620HW'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/whirlpool/WTW5057LW'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/whirlpool/WFW6620HW'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/whirlpool/WTW8127LW'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/whirlpool/WTW4855HW'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/whirlpool/WED5620HW'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/whirlpool/WGD5050LW'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/whirlpool/WED6120HW'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/whirlpool/WED8127LW'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/whirlpool/WGD5605MW'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/whirlpool/WFE525S0JZ'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/whirlpool/WFG525S0JZ'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/whirlpool/WEE750H0HZ'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/whirlpool/WFE505W0JS'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/whirlpool/WFG550S0LZ'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/whirlpool/WDT730PAHZ'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/whirlpool/WDTA50SAKZ'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/whirlpool/WDT750SAKZ'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/whirlpool/WDF540PADM'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/whirlpool/WDT970SAHZ'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/whirlpool/WMH31017HZ'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/whirlpool/WMH53521HZ'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/whirlpool/WML55011HS'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/whirlpool/WMH32519HT'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/whirlpool/WMC30516HZ'
