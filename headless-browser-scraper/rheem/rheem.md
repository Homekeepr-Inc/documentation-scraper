# Rheem Headless Scraper

This scraper uses DuckDuckGo fallback as the primary method to find Rheem water heater manuals on rheem.com, with homedepot.com as fallback.

## How it works
- **Primary**: Searches DuckDuckGo for the model number on rheem.com
  - Navigates to the product page
  - Verifies the model number is present in the page content
  - Scrolls down and clicks the second accordion button to expand literature
  - Clicks the "Use and Care Instructions" link (opens literature page)
  - On the literature page, clicks "Use and Care Instructions" again to download the PDF
- **Fallback**: If primary fails, searches DuckDuckGo for the model number on homedepot.com
  - Navigates to the product page
  - Verifies the model number is present in the page content
  - Clicks "Product Details" to expand the section
  - Clicks the "Use and Care Manual" link to download the PDF

## Usage
Run the scraper directly:
```bash
python3 rheem_headless_scraper.py <model_number>
```

Or via API:
```
GET /scrape/rheem/{model}
```

## Notes
- Model normalization: Replaces "/" with "_"
- Uses undetected-chromedriver for stealth
- Downloads to temp directory, validates PDF, ingests to DB


curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" "http://localhost:8000/scrape/rheem/XG40T06EN38U1" &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" "http://localhost:8000/scrape/rheem/ECO200XELN-3" &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" "http://localhost:8000/scrape/rheem/XE40M06ST45U1" &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" "http://localhost:8000/scrape/rheem/XG50T06EC38U1" &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" "http://localhost:8000/scrape/rheem/PROG50-42N-RU67-PV" &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" "http://localhost:8000/scrape/rheem/XG40T12HE40U0" &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" "http://localhost:8000/scrape/rheem/RTGH-95DVLN-3" &
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" "http://localhost:8000/scrape/rheem/RTG-95XLN-1" 