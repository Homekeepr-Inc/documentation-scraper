import json
from typing import Iterable

import scrapy

IA_SEARCH = "https://archive.org/advancedsearch.php"
IA_ITEM = "https://archive.org/metadata/{identifier}"


class IaSpider(scrapy.Spider):
    name = "ia"

    def __init__(self, brand: str = "whirlpool", rows: int = 50, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.brand = brand
        self.rows = int(rows)

    def start_requests(self) -> Iterable[scrapy.Request]:
        query = f'(title:"{self.brand}" OR description:"{self.brand}") AND (format:PDF)'
        params = {
            "q": query,
            "fl[]": ["identifier", "title", "mediatype"],
            "rows": self.rows,
            "output": "json",
        }
        url = IA_SEARCH + "?" + scrapy.utils.python.to_unicode(scrapy.http.request.form._urlencode(params))
        yield scrapy.Request(url, callback=self.parse_search, headers={"Accept": "application/json"})

    def parse_search(self, response: scrapy.http.Response):
        data = json.loads(response.text)
        docs = data.get("response", {}).get("docs", [])
        for d in docs:
            identifier = d.get("identifier")
            if not identifier:
                continue
            yield scrapy.Request(IA_ITEM.format(identifier=identifier), callback=self.parse_item, cb_kwargs={"identifier": identifier})

    def parse_item(self, response: scrapy.http.Response, identifier: str):
        meta = json.loads(response.text)
        files = meta.get("files", [])
        title = meta.get("metadata", {}).get("title") or identifier
        pdfs = [f for f in files if f.get("format", "").lower() == "text pdf" or (f.get("name", "").lower().endswith(".pdf"))]
        if not pdfs:
            return
        pdfs.sort(key=lambda f: f.get("size", 0), reverse=True)
        pdf = pdfs[0]
        file_url = f"https://archive.org/download/{identifier}/{pdf.get('name')}"
        yield {
            "brand": self.brand,
            "model_number": "unknown",
            "doc_type": "service",
            "title": title,
            "source_url": f"https://archive.org/details/{identifier}",
            "file_url": file_url,
        }
