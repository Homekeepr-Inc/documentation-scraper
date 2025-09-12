"""
TODO: BROKEN SPIDER - ManualsLib CSS selectors need debugging

Issues:
- CSS selectors 'a[href*="/manual/"]' don't match actual page structure
- Search results may be dynamically loaded via JavaScript
- Need to inspect actual HTML structure

Potential fixes:
1. Use browser dev tools to find correct selectors for manual links
2. May need Playwright for JS-rendered content
3. Try different search URL patterns
4. Check if they have an API or RSS feed

High value target: ManualsLib claims 3+ million manuals
"""

import re
from typing import Iterable

import scrapy


class ManualslibSpider(scrapy.Spider):
    name = "manualslib"
    custom_settings = {
        'ROBOTSTXT_OBEY': False,  # ManualsLib typically allows this
        'DOWNLOAD_DELAY': 1,
        'CONCURRENT_REQUESTS': 4,
    }

    def __init__(self, brand: str = "whirlpool", category: str = "washer", limit: int = 50, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.brand = brand.lower()
        self.category = category.lower()
        self.limit = int(limit)
        self.count = 0

    def start_requests(self) -> Iterable[scrapy.Request]:
        # ManualsLib search by brand and category
        search_url = f"https://www.manualslib.com/search/{self.brand}+{self.category}"
        yield scrapy.Request(search_url, callback=self.parse_search)

    def parse_search(self, response: scrapy.http.Response):
        # Extract manual page links
        for href in response.css('a[href*="/manual/"]::attr(href)').getall():
            if self.count >= self.limit:
                break
            manual_url = response.urljoin(href)
            self.count += 1
            yield scrapy.Request(manual_url, callback=self.parse_manual)

        # Follow pagination
        next_page = response.css('a.next-page::attr(href)').get()
        if next_page and self.count < self.limit:
            yield scrapy.Request(response.urljoin(next_page), callback=self.parse_search)

    def parse_manual(self, response: scrapy.http.Response):
        title = response.css('h1::text').get() or ""
        
        # Extract brand and model from title or page
        brand = self.brand
        model_match = re.search(r'model[:\s]+([A-Z0-9\-]+)', title, re.I)
        model_number = model_match.group(1) if model_match else "unknown"
        
        # Look for PDF download links
        pdf_links = []
        for a in response.css('a[href$=".pdf"]::attr(href)').getall():
            pdf_links.append(response.urljoin(a))
        
        # Also check for ManualsLib's PDF viewer links
        for a in response.css('a[href*="/pdf/"]::attr(href)').getall():
            pdf_links.append(response.urljoin(a))

        for pdf_url in pdf_links:
            doc_type = self._infer_doc_type(pdf_url, title)
            yield {
                "brand": brand,
                "model_number": model_number,
                "doc_type": doc_type,
                "title": title,
                "source_url": response.url,
                "file_url": pdf_url,
            }

    def _infer_doc_type(self, url: str, title: str = "") -> str:
        text = (url + " " + title).lower()
        if any(x in text for x in ["service", "tech", "wiring", "schematic", "diagnostic", "repair"]):
            if "tech" in text:
                return "tech_sheet"
            if "wiring" in text or "schematic" in text:
                return "wiring"
            return "service"
        if "install" in text or "installation" in text:
            return "install"
        if "spec" in text or "specification" in text:
            return "spec"
        return "owner"
