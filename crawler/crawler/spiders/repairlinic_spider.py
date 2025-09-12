import re
from typing import Iterable

import scrapy


class RepairClinicSpider(scrapy.Spider):
    name = "repairlinic"
    custom_settings = {
        'ROBOTSTXT_OBEY': False,  # Bypass robots for manual collection
        'DOWNLOAD_DELAY': 0.75,
        'CONCURRENT_REQUESTS': 4,
    }

    def __init__(self, brand: str = "whirlpool", appliance: str = "washer", limit: int = 50, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.brand = brand.lower()
        self.appliance = appliance.lower()
        self.limit = int(limit)
        self.count = 0

    def start_requests(self) -> Iterable[scrapy.Request]:
        # RepairClinic search
        search_url = f"https://www.repairclinic.com/Search?q={self.brand}+{self.appliance}"
        yield scrapy.Request(search_url, callback=self.parse_search)

    def parse_search(self, response: scrapy.http.Response):
        # Extract model page links
        for href in response.css('a[href*="/Model/"]::attr(href)').getall():
            if self.count >= self.limit:
                break
            model_url = response.urljoin(href)
            self.count += 1
            yield scrapy.Request(model_url, callback=self.parse_model)

        # Follow pagination
        next_page = response.css('a[aria-label="Next"]::attr(href)').get()
        if next_page and self.count < self.limit:
            yield scrapy.Request(response.urljoin(next_page), callback=self.parse_search)

    def parse_model(self, response: scrapy.http.Response):
        title = response.css('h1::text').get() or ""
        
        # Extract model number from URL or title
        model_match = re.search(r'/Model/([A-Z0-9\-]+)', response.url) or re.search(r'Model[:\s]+([A-Z0-9\-]+)', title, re.I)
        model_number = model_match.group(1) if model_match else "unknown"
        
        # Look for manual/literature links
        pdf_links = set()
        
        # Direct PDF links
        for a in response.css('a[href$=".pdf"]::attr(href)').getall():
            pdf_links.add(response.urljoin(a))
        
        # Manual/literature section links
        for a in response.css('a[href*="manual"], a[href*="literature"], a[href*="guide"]').getall():
            href = response.css(f'a[href*="{a}"]::attr(href)').get()
            if href and href.lower().endswith('.pdf'):
                pdf_links.add(response.urljoin(href))

        for pdf_url in pdf_links:
            doc_type = self._infer_doc_type(pdf_url, title)
            yield {
                "brand": self.brand,
                "model_number": model_number,
                "doc_type": doc_type,
                "title": title or f"{self.brand} {model_number} manual",
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
