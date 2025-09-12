"""
TODO: BROKEN SPIDER - Sears PartsDirect returns 403 Forbidden

Issues:
- Returns 403 even with realistic browser headers
- May have IP-based blocking or require session cookies
- Cloudflare or similar protection

Potential fixes:
1. Use residential proxy rotation
2. Research session/cookie requirements
3. Try mobile site (m.searspartsdirect.com)
4. Use Playwright with full browser context
5. Try different entry points (direct model URLs)

High value target: Sears has extensive model database with manual links
"""

import json
import re
from typing import Iterable

import scrapy

SEARCH_URL = "https://www.searspartsdirect.com/model/search?q={query}"


class SearsSpider(scrapy.Spider):
    name = "sears"
    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'DOWNLOAD_DELAY': 1.0,
        'CONCURRENT_REQUESTS': 2,
        'DEFAULT_REQUEST_HEADERS': {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
    }

    def __init__(self, brand: str = "kenmore", query: str = "washer", limit: int = 50, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.brand = brand
        self.query = query
        self.limit = int(limit)
        self.count = 0

    def start_requests(self) -> Iterable[scrapy.Request]:
        url = SEARCH_URL.format(query=scrapy.utils.python.to_unicode(self.query))
        yield scrapy.Request(url, callback=self.parse_search, headers=self.custom_settings['DEFAULT_REQUEST_HEADERS'])

    def parse_search(self, response: scrapy.http.Response):
        # Extract model links from search results
        for href in response.css('a[href*="/model/" ]::attr(href)').getall():
            if self.count >= self.limit:
                break
            if not href.startswith("http"):
                href = response.urljoin(href)
            self.count += 1
            yield scrapy.Request(href, callback=self.parse_model)

        # Follow pagination if present
        next_href = response.css('a[aria-label="Next"]::attr(href)').get()
        if next_href and self.count < self.limit:
            yield scrapy.Request(response.urljoin(next_href), callback=self.parse_search)

    def parse_model(self, response: scrapy.http.Response):
        title = response.css("h1::text").get() or ""
        model_number = response.css('div:contains("Model #") strong::text').get() or "unknown"
        brand = self.brand or (response.css('div:contains("Brand") strong::text').get() or "sears")

        # Look for literature/manual links
        pdf_links = set()
        for a in response.css('a[href$=".pdf"]::attr(href)').getall():
            pdf_links.add(response.urljoin(a))

        # Sometimes JSON data embedded
        for script in response.css("script::text").getall():
            if 'pdf' in script.lower():
                for m in re.finditer(r'https?://[^"\s]+\.pdf', script, flags=re.I):
                    pdf_links.add(m.group(0))

        for file_url in pdf_links:
            doc_type = self._infer_doc_type(file_url)
            yield {
                "brand": brand.lower(),
                "model_number": model_number,
                "doc_type": doc_type,
                "title": title or f"{brand} {model_number} manual",
                "source_url": response.url,
                "file_url": file_url,
            }

    def _infer_doc_type(self, url: str) -> str:
        u = url.lower()
        if any(x in u for x in ["service", "tech", "sheet", "wiring"]):
            if "tech" in u or "techsheet" in u or "tech-sheet" in u:
                return "tech_sheet"
            if "wiring" in u:
                return "wiring"
            return "service"
        if "install" in u or "installation" in u:
            return "install"
        if "spec" in u or "specification" in u:
            return "spec"
        return "owner"
