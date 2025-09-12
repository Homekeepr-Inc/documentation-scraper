"""
TODO: BROKEN SPIDER - Whirlpool JSON endpoint timeouts

Issues:
- JSON endpoint https://www.whirlpool.com/services/_jcr_content.manuals.search.json times out
- Robots.txt fetch also times out
- Site appears to have anti-bot protection

Potential fixes:
1. Use residential proxy rotation
2. Try mobile endpoints (m.whirlpool.com)
3. Sitemap crawling (already implemented in sitemap_spider.py)
4. CDN pattern discovery for direct PDF URLs
5. Archive.today/Wayback Machine for cached pages

Current workaround: Use sitemap_spider.py and Internet Archive
"""

import json
from typing import Iterable, List

import scrapy


class WhirlpoolSpider(scrapy.Spider):
    name = "whirlpool"
    custom_settings = {
        'ROBOTSTXT_OBEY': False,  # Bypass robots.txt timeout issues
        'DOWNLOAD_TIMEOUT': 15,
    }

    def __init__(self, models: str = "", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_numbers: List[str] = [m.strip() for m in models.split(",") if m.strip()]

    def start_requests(self) -> Iterable[scrapy.Request]:
        # Use Whirlpool's JSON search endpoint
        for model in self.model_numbers:
            url = f"https://www.whirlpool.com/services/_jcr_content.manuals.search.json?q={model}"
            yield scrapy.Request(
                url=url,
                callback=self.parse_search,
                cb_kwargs={"model": model},
                headers={"Accept": "application/json"},
            )

    def parse_search(self, response: scrapy.http.Response, model: str):
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            return

        # Parse manuals from JSON response
        manuals = data.get("manuals", []) or data.get("results", [])
        for manual in manuals:
            title = manual.get("title", "") or manual.get("name", "")
            pdf_url = manual.get("url", "") or manual.get("pdfUrl", "")
            
            if not pdf_url:
                continue
                
            if not pdf_url.startswith("http"):
                pdf_url = f"https://www.whirlpool.com{pdf_url}"

            doc_type = self._infer_doc_type(pdf_url, title)
            
            yield {
                "brand": "whirlpool",
                "model_number": model,
                "doc_type": doc_type,
                "title": title or f"Whirlpool {model} manual",
                "source_url": f"https://www.whirlpool.com/services/manuals.html?model={model}",
                "file_url": pdf_url,
            }

    def _infer_doc_type(self, url: str, title: str = "") -> str:
        text = (url + " " + title).lower()
        if any(x in text for x in ["service", "tech", "wiring", "schematic", "diagnostic"]):
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