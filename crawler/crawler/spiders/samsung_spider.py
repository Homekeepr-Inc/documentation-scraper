from typing import Iterable, List

import scrapy
from scrapy_playwright.page import PageMethod


class SamsungSpider(scrapy.Spider):
    name = "samsung"

    def __init__(self, models: str = "", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model_numbers: List[str] = [m.strip() for m in models.split(",") if m.strip()]

    def start_requests(self) -> Iterable[scrapy.Request]:
        base = "https://www.samsung.com/us/support/"
        for model in self.model_numbers:
            yield scrapy.Request(
                url=base,
                callback=self.parse_search,
                cb_kwargs={"model": model},
                meta={
                    "playwright": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_selector", "input[type=search]"),
                        PageMethod("fill", "input[type=search]", model),
                        PageMethod("press", "input[type=search]", "Enter"),
                        PageMethod("wait_for_timeout", 2500),
                    ],
                },
            )

    def parse_search(self, response: scrapy.http.Response, model: str):
        links = response.css('a[href$=".pdf"]::attr(href)').getall()
        title = response.css("title::text").get() or f"Samsung {model} manual"
        for href in links:
            file_url = response.urljoin(href)
            yield {
                "brand": "samsung",
                "model_number": model,
                "doc_type": self._infer_doc_type(file_url),
                "title": title,
                "source_url": response.url,
                "file_url": file_url,
            }

    def _infer_doc_type(self, url: str) -> str:
        u = url.lower()
        if any(x in u for x in ["service", "tech", "wiring", "schematic", "diagnostic"]):
            if "tech" in u:
                return "tech_sheet"
            if "wiring" in u or "schematic" in u:
                return "wiring"
            return "service"
        if "install" in u or "installation" in u:
            return "install"
        if "spec" in u:
            return "spec"
        return "owner"
