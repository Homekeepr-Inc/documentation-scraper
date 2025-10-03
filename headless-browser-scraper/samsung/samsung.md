# Samsung Appliance Manuals Scraper

This scraper extracts owner's manuals from samsung.com for specific model numbers using a headless browser.

## URL Pattern
The scraper starts at a generic support page and searches for the model:
`https://www.samsung.com/latin_en/support/user-manuals-and-guide/`

## PDF Extraction
The process involves several steps driven by Selenium:
1.  Navigate to the support page.
2.  Enter the model number into the search input (`#sud13-code-search-input`).
3.  Click the search button.
4.  From the search results, click the link corresponding to the model number, identified by `a[data-modelcode="{model}"]`.
5.  Click the first option in the resulting dropdown (`.sud13-select-option:nth-child(1)`).
6.  Click the "Download" link to initiate the PDF download.

## Example HTML Elements
### Search Result Link
```html
<ul class="sud13-search__suggested-list sdf-comp-search-model-panel">
  <li class="sud13-search__suggested-item">
    <a href="javascript:void(0)" data-modelcode="RF29DB9900QDAA" ...>
      RF29DB9900QD (<b>RF29DB9900QDAA</b>)
    </a>
  </li>
</ul>
```

## Step-by-Step Scraping Process

1.  **URL Construction**: Start at the main support page.
2.  **Headless Browser Initialization**: Launch `undetected-chromedriver` with stealth options and download preferences.
3.  **Page Fetch**: Navigate to the URL and wait for the page to load.
4.  **Search**: Input the model number and submit the search form.
5.  **Model Selection**: Wait for search results and click the correct model link.
6.  **PDF Extraction**: Select the first option and click the "Download" link.
7.  **Download and Validation**: Wait for the file to be downloaded to the specified directory and validate it by checking if the content starts with `%PDF-`.
8.  **Data Collection**: Collect metadata:
    *   `brand`: "samsung"
    *   `model_number`: The model number.
    *   `doc_type`: "owner" (default).
    *   `title`: "Samsung {model} manual"
    *   `source_url`: The page URL.
    *   `file_url`: The direct PDF URL.
    *   `local_path`: The local path of the downloaded file.
9.  **Ingestion**: Pass data to an ingestion function for duplicate checking and storage.

## How to Run

```bash
python3 headless-browser-scraper/samsung_headless_scraper.py RF29DB9900QDAA
```

It downloads the PDF locally and ingests it into the database.

## Example Model Numbers

curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/samsung/RF29A9671SR/AA'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/samsung/RF23A9671SR/AA'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/samsung/RF27T5501SR/AA'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/samsung/RF28R7351SG/AA'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/samsung/RS27T5200SR/AA'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/samsung/WV60A9900AV/A5'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/samsung/WF53BB8900AD/US'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/samsung/WF46BG6500AV/US'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/samsung/WA54CG7550AV/US'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/samsung/WV50A9465AV/A5'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/samsung/DVE53BB8900D/A3'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/samsung/DVG46BG6500V/A3'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/samsung/DVE50A8600V/A3'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/samsung/DVE60A9900V/A3'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/samsung/DVG54CG7550V/A3'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/samsung/NE63A8711SG/AA'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/samsung/NX60T8711SS/AA'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/samsung/NE63T8511SS/AA'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/samsung/NY63T8751SS/AA'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/samsung/NE63BB871112/AA'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/samsung/DW50T6060US/AA'
