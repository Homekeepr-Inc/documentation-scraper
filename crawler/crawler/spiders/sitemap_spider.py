import re
from typing import Iterable
from urllib.parse import urljoin

import scrapy


class SitemapSpider(scrapy.Spider):
    name = "sitemap"
    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'DOWNLOAD_DELAY': 0.5,
        'CONCURRENT_REQUESTS': 8,
    }

    def __init__(self, brand: str = "ge", limit: int = 100, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.brand = brand.lower()
        self.limit = int(limit)
        self.count = 0

    def start_requests(self) -> Iterable[scrapy.Request]:
        # Brand-specific sitemap URLs
        sitemaps = {
            "ge": [
                "https://products.geappliances.com/sitemap.xml",
                "https://www.geappliances.com/sitemap.xml",
            ],
            "whirlpool": [
                "https://www.whirlpool.com/sitemap.xml",
                "https://www.whirlpool.com/sitemap_index.xml",
            ],
            "lg": [
                "https://www.lg.com/us/sitemap.xml",
            ],
            "samsung": [
                "https://www.samsung.com/us/sitemap.xml",
            ],
        }
        
        for sitemap_url in sitemaps.get(self.brand, []):
            yield scrapy.Request(sitemap_url, callback=self.parse_sitemap)

    def parse_sitemap(self, response: scrapy.http.Response):
        # Parse XML sitemap
        namespaces = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        
        # Check if this is a sitemap index (contains other sitemaps)
        sitemap_refs = response.xpath('//ns:sitemap/ns:loc/text()', namespaces=namespaces).getall()
        if sitemap_refs:
            for sitemap_url in sitemap_refs:
                if self.count < self.limit:
                    yield scrapy.Request(sitemap_url, callback=self.parse_sitemap)
                    self.count += 1
            return

        # Parse individual URLs from sitemap
        urls = response.xpath('//ns:url/ns:loc/text()', namespaces=namespaces).getall()
        
        for url in urls:
            if self.count >= self.limit:
                break
                
            # Filter for manual/PDF related URLs
            if any(keyword in url.lower() for keyword in ['manual', 'pdf', 'literature', 'document', 'support']):
                self.count += 1
                yield scrapy.Request(url, callback=self.parse_manual_page)

    def parse_manual_page(self, response: scrapy.http.Response):
        # Extract PDF links from manual/support pages
        pdf_links = set()
        
        # Direct PDF links
        for href in response.css('a[href$=".pdf"]::attr(href)').getall():
            pdf_links.add(response.urljoin(href))
        
        # Links containing "manual", "literature", etc.
        for a in response.css('a[href*="manual"], a[href*="literature"], a[href*="document"]'):
            href = a.css('::attr(href)').get()
            if href and href.lower().endswith('.pdf'):
                pdf_links.add(response.urljoin(href))
        
        # Check for embedded JSON with PDF URLs (common pattern)
        for script in response.css('script::text').getall():
            if 'pdf' in script.lower():
                for match in re.finditer(r'https?://[^"\s]+\.pdf', script, re.I):
                    pdf_links.add(match.group(0))

        # Extract model number from URL or page content
        model_number = self._extract_model(response.url, response.text)
        title = response.css('title::text').get() or response.css('h1::text').get() or ""

        for pdf_url in pdf_links:
            doc_type = self._infer_doc_type(pdf_url, title)
            yield {
                "brand": self.brand,
                "model_number": model_number,
                "doc_type": doc_type,
                "equipment_category": "appliance",
                "equipment_type": "unknown",
                "title": title or f"{self.brand} {model_number} manual",
                "source_url": response.url,
                "file_url": pdf_url,
            }

    def _extract_model(self, url: str, text: str) -> str:
        """Extract model number from URL or page text."""
        # Try URL first
        url_match = re.search(r'/([A-Z0-9\-]{4,})/?', url)
        if url_match:
            return url_match.group(1)
        
        # Try page text
        text_match = re.search(r'[Mm]odel[:\s]+([A-Z0-9\-]{4,})', text)
        if text_match:
            return text_match.group(1)
            
        return "unknown"

    def _infer_doc_type(self, url: str, title: str = "") -> str:
        """Infer document type from URL and title."""
        text = (url + " " + title).lower()
        if any(x in text for x in ["service", "tech", "wiring", "schematic", "diagnostic"]):
            if "tech" in text or "specification" in text:
                return "tech_sheet"
            if "wiring" in text or "schematic" in text:
                return "wiring"
            return "service"
        if "install" in text or "installation" in text:
            return "install"
        if "spec" in text:
            return "spec"
        return "owner"
