# Rheem Headless Scraper

This scraper uses DuckDuckGo fallback as the primary method to find Rheem water heater manuals on homedepot.com.

## How it works
- **Primary**: Searches DuckDuckGo for the model number on homedepot.com
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


curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" "http://localhost:8000/scrape/rheem/XG40T06EN38U1"