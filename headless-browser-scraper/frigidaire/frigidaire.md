# Frigidaire Headless Scraper

This scraper extracts owner's manual PDFs from Frigidaire's website using headless browser automation.

## URL Pattern

The scraper uses a direct URL approach:
`https://www.frigidaire.com/en/p/owner-center/product-support/{model}`

Replace {model} with the appliance model number (e.g., FPFU19F8WF). The page redirects to the actual product page.

## PDF Extraction

The scraper finds manual links using CSS selectors and prioritizes owner's manuals:

1. Find all elements with `.mannual-name` class (manual download links)
2. Identify owner's manuals using keywords: "owner", "complete owner", "user guide"
3. Prioritize owner's manuals over specification sheets and installation guides
4. Select the highest priority document for download

## Example HTML Elements

### Manual Links Container
```html
<div class="row mt-2 manuals">
  <div class="col-10 Body-MediumBody_Medium-Link">
    <a class="mannual-name" href="https://na2.electroluxmedia.com/Original/Electrolux/Electrolux%20Assets/Document/Complete%20Owners%20Guide/English/A16366306en.pdf">
      Complete Owner's Guide
    </a>
  </div>
  <div class="col-2">
    <a class="mannual-name" href="https://na2.electroluxmedia.com/Original/Electrolux/Electrolux%20Assets/Document/Complete%20Owners%20Guide/English/A16366306en.pdf">
      <img src="/assets/images/frg-icons-download-f-33-d.png" alt="Download Arrow" loading="lazy">
    </a>
  </div>
</div>
```

### Other Document Types Found
- Product Specifications Sheet
- Energy Guide
- Installation Instructions
- Quick Start Guide

## Step-by-Step Scraping Process

1. **URL Construction**: Build direct URL as `https://www.frigidaire.com/en/p/owner-center/product-support/{model}`

2. **Headless Browser Initialization**: Launch `undetected-chromedriver` in headless mode with stealth options and download preferences

3. **Page Navigation**: Navigate to the URL and wait for page load/redirect to complete

4. **Manual Link Discovery**: Find all `.mannual-name` elements containing PDF links

5. **Document Prioritization**:
   - Identify owner's manuals using keyword matching
   - Sort documents with owner's manuals first
   - Select highest priority document

6. **Download and Validation**: Download the selected PDF and validate by checking if content starts with `%PDF-`

7. **Data Collection**: Collect metadata:
   * `brand`: "frigidaire"
   * `model_number`: The normalized model number
   * `doc_type`: "owner"
   * `title`: The document title (e.g., "Complete Owner's Guide")
   * `source_url`: The product page URL
   * `file_url`: The PDF download URL

8. **Ingestion**: Pass data to ingestion function for duplicate checking and storage

## Features

- **Headless Operation**: Uses undetected-chromedriver for stealthy scraping
- **Smart Document Selection**: Automatically prioritizes owner's manuals over specs/installation guides
- **Direct URL Approach**: Bypasses complex search workflows for efficiency and reliability
- **Error Handling**: JavaScript clicks to avoid element interception issues
- **Fallback Support**: Uses DuckDuckGo fallback if primary scraping fails
- **PDF Validation**: Validates downloaded files are actual PDFs
- **Caching**: Integrates with the global caching system via model normalization

## How to Run

```bash
python3 headless-browser-scraper/frigidaire/frigidaire_headless_scraper.py FPFU19F8WF
```

It downloads the PDF locally and ingests it into the database.

## Example Model Numbers

curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/frigidaire/FPFU19F8WF
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/frigidaire/FFTR2021TS
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/frigidaire/FGTR2045QF
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/frigidaire/FGHB2868TF
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/frigidaire/FGHS2631PF
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/frigidaire/FGHS2655PF
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/frigidaire/FGTR1845QF
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/frigidaire/FPFU19F8WF
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/frigidaire/FGTR2042QF
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/frigidaire/FGHB2844LF
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/frigidaire/FGHS2342LF
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/frigidaire/FGTR1842QF
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/frigidaire/FGHB2869LF
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/frigidaire/FGHS2669KF
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/frigidaire/FGTR2047QF
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/frigidaire/FGHB2844LM
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/frigidaire/FGHS2342LM
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/frigidaire/FGTR1842QM
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/frigidaire/FGHB2869LM
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/frigidaire/FGHS2669KM
curl -H "X-Homekeepr-Scraper: $SCRAPER_SECRET" http://localhost:8000/scrape/frigidaire/FGTR2047QM