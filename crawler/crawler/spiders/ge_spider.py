"""
TODO: BROKEN SPIDER - GE JSON endpoint issues

Issues:
- JSON endpoint https://products.geappliances.com/appliance/gea-support-search-content doesn't return expected format
- PDF dispatcher URLs may require authentication
- Connection timeouts

Potential fixes:
1. Research actual GE API endpoints used by their website
2. Try different search parameters or headers
3. Use sitemap crawling (already working in sitemap_spider.py)
4. Parse HTML search results instead of JSON

Current workaround: Use sitemap_spider.py and Internet Archive
"""

import json
from typing import Iterable, List

import scrapy


class GESpider(scrapy.Spider):
    name = "ge"

    def __init__(self, models: str = "", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_numbers: List[str] = [m.strip() for m in models.split(",") if m.strip()]

    def start_requests(self) -> Iterable[scrapy.Request]:
        # Use GE's JSON search endpoint
        for model in self.model_numbers:
            url = f"https://products.geappliances.com/appliance/gea-support-search-content?searchText={model}"
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
        docs = data.get("documents", []) or data.get("results", [])
        for doc in docs:
            title = doc.get("title", "") or doc.get("name", "")
            doc_name = doc.get("fileName", "") or doc.get("documentName", "")
            
            if not doc_name or not doc_name.lower().endswith(".pdf"):
                continue
                
            # GE PDF pattern
            pdf_url = f"https://products.geappliances.com/MarketingObjectRetrieval/Dispatcher?RequestType=PDF&Name={doc_name}"

            doc_type = self._infer_doc_type(doc_name, title)
            
            yield {
                "brand": "ge",
                "model_number": model,
                "doc_type": doc_type,
                "title": title or f"GE {model} manual",
                "source_url": f"https://www.geappliances.com/ge/appliance/gea-manuals?model={model}",
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