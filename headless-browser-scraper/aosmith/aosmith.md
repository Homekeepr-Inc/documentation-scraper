# A.O. Smith Headless Scraper

This scraper uses DuckDuckGo fallback as the primary method to find A.O. Smith appliance manuals on aosmithatlowes.com.

## How it works
- **Primary**: Searches DuckDuckGo for the model number on aosmithatlowes.com
  - Navigates to the product page
  - Scrolls down and locates the Owners Manual link directly
  - Extracts the PDF URL and navigates to it for download
- **Fallback**: If primary fails, searches DuckDuckGo for the model (without site restriction)
  - Clicks the first result linking to hotwater.com
  - Navigates to the product page
  - If "Series Discontinued" is detected, clicks the literature link (downloads PDF directly)
  - Otherwise, clicks the "Product Literature" tab, then the first "Manual" link (opens PDF in new window)

## Usage
Run the scraper directly:
```bash
python3 aosmith_headless_scraper.py <model_number>
```

Or via API:
```
GET /scrape/aosmith/{model}
```

## Notes
- Model normalization: Replaces "/" with "_"
- Uses undetected-chromedriver for stealth
- Downloads to temp directory, validates PDF, ingests to DB


curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" "http://localhost:8000/scrape/aosmith/E6-50H45DV" &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" "http://localhost:8000/scrape/aosmith/BTH-199 300" &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" "http://localhost:8000/scrape/aosmith/ATI-540H-100" &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" "http://localhost:8000/scrape/aosmith/GPVL-50" &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" "http://localhost:8000/scrape/aosmith/FPTU-50" &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" "http://localhost:8000/scrape/aosmith/GPD-40L" &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" "http://localhost:8000/scrape/aosmith/GPD-50L" &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" "http://localhost:8000/scrape/aosmith/GPD-75L" &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" "http://localhost:8000/scrape/aosmith/ECT-52" &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" "http://localhost:8000/scrape/aosmith/SHPT-50" 