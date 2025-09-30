# Rheem Headless Scraper

This scraper uses DuckDuckGo fallback as the primary method to find Rheem water heater manuals on rheem.com, with homedepot.com and supplyhouse.com as fallbacks.

## How it works
- **Primary**: Searches DuckDuckGo for the model number on rheem.com
  - Navigates to the product page
  - Verifies the model number is present in the page content
  - Scrolls down and clicks the second accordion button to expand literature
  - Clicks the "Use and Care Instructions" link (opens literature page)
  - On the literature page, clicks "Use and Care Instructions" again to download the PDF
- **Fallback 1**: If primary fails, searches DuckDuckGo for the model number on homedepot.com
  - Navigates to the product page
  - Verifies the model number is present in the page content
  - Clicks "Product Details" to expand the section
  - Clicks the "Use and Care Manual" link to download the PDF. If the click is intercepted, it navigates to the href directly.
- **Fallback 2**: If homedepot.com fails, searches DuckDuckGo for the model number on supplyhouse.com
  - Navigates to the product page
  - Verifies the model number is present in the page content
  - Clicks the link to the user manual to download the PDF.

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


curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/rheem/XG40T06EN38U1'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/rheem/ECO200XELN-3'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/rheem/XE40M06ST45U1'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/rheem/XG50T06EC38U1'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/rheem/PROG50-42N-RU67-PV'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/rheem/XG40T12HE40U0'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/rheem/RTGH-95DVLN-3'
curl -k -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" 'https://localhost/scrape/rheem/RTG-95XLN-1'
