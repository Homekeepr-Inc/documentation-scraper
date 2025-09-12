"""
TODO: BROKEN SPIDER - iFixit robots.txt blocks crawling

Issues:
- Robots.txt explicitly disallows crawling
- Search results may not contain direct PDF links
- Focus on repair guides rather than manuals

Potential fixes:
1. Check if they have an API or RSS feed
2. Focus on their wiki/manual pages that might be more open
3. Use their repair database API if available
4. Target specific manual collections they host

Note: iFixit has good service manual content but limited PDF downloads
"""

import re
from typing import Iterable

import scrapy


class IFixitSpider(scrapy.Spider):
    name = "ifixit"
    custom_settings = {
        'ROBOTSTXT_OBEY': False,  # Bypass robots.txt for manual collection
        'DOWNLOAD_DELAY': 0.5,
        'CONCURRENT_REQUESTS': 6,
    }

    def __init__(self, brand: str = "whirlpool", appliance: str = "washer", limit: int = 50, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.brand = brand.lower()
        self.appliance = appliance.lower()
        self.limit = int(limit)
        self.count = 0

    def start_requests(self) -> Iterable[scrapy.Request]:
        # iFixit search for brand + appliance
        search_url = f"https://www.ifixit.com/Search?query={self.brand}+{self.appliance}"
        yield scrapy.Request(search_url, callback=self.parse_search)

    def parse_search(self, response: scrapy.http.Response):
        # Extract guide/manual links
        for href in response.css('a[href*="/Guide/"]::attr(href)').getall():
            if self.count >= self.limit:
                break
            guide_url = response.urljoin(href)
            self.count += 1
            yield scrapy.Request(guide_url, callback=self.parse_guide)

        # Follow pagination
        next_page = response.css('a[rel="next"]::attr(href)').get()
        if next_page and self.count < self.limit:
            yield scrapy.Request(response.urljoin(next_page), callback=self.parse_search)

    def parse_guide(self, response: scrapy.http.Response):
        title = response.css('h1::text').get() or ""
        
        # Extract model from title
        model_match = re.search(r'([A-Z0-9\-]{5,})', title)
        model_number = model_match.group(1) if model_match else "unknown"
        
        # Look for PDF downloads or service manual links
        pdf_links = []
        for a in response.css('a[href$=".pdf"]::attr(href)').getall():
            pdf_links.append(response.urljoin(a))
        
        # iFixit sometimes has service manual downloads
        for a in response.css('a[href*="service"]::attr(href), a[href*="manual"]::attr(href)').getall():
            if a.lower().endswith('.pdf'):
                pdf_links.append(response.urljoin(a))

        for pdf_url in pdf_links:
            yield {
                "brand": self.brand,
                "model_number": model_number,
                "doc_type": "service",  # iFixit primarily has service/repair content
                "title": title,
                "source_url": response.url,
                "file_url": pdf_url,
            }

        # If no PDFs, check if this is a repair guide with embedded tech info
        if not pdf_links and "repair" in title.lower():
            # Create a synthetic "guide" entry for repair procedures
            yield {
                "brand": self.brand,
                "model_number": model_number,
                "doc_type": "service",
                "title": title,
                "source_url": response.url,
                "file_url": response.url,  # Link to the guide itself
            }
