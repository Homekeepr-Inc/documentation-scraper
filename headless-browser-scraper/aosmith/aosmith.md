# A.O. Smith Headless Scraper

This scraper uses DuckDuckGo fallback as the primary method to find A.O. Smith appliance manuals on aosmithatlowes.com.

## How it works
- Searches DuckDuckGo for the model number on aosmithatlowes.com
- Navigates to the product page
- Scrolls down and clicks the "Use & Care Instructions" tabcordion section to expand it
- Extracts the Owners Manual PDF URL from the expanded content
- Navigates directly to the PDF URL to download the manual

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