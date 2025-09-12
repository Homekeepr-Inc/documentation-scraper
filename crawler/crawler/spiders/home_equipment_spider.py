from typing import Iterable

import scrapy


class HomeEquipmentSpider(scrapy.Spider):
    name = "home_equipment"
    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'DOWNLOAD_DELAY': 0.5,
        'CONCURRENT_REQUESTS': 6,
    }

    def __init__(self, category: str = "hvac", equipment: str = "furnace", brand: str = "", limit: int = 50, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.category = category.lower()
        self.equipment = equipment.lower()
        self.brand = brand.lower() if brand else ""
        self.limit = int(limit)

    def start_requests(self) -> Iterable[scrapy.Request]:
        # Create comprehensive IA query for home equipment
        equipment_terms = self._get_equipment_terms()
        brand_terms = f"AND {self.brand}" if self.brand else ""
        manual_terms = "(manual OR \"owner's manual\" OR service OR \"tech sheet\" OR installation OR guide OR instructions)"
        
        query = f"collection:manuals AND {equipment_terms} {brand_terms} AND {manual_terms}"
        
        url = f"https://archive.org/advancedsearch.php?q={query}&fl[]=identifier&fl[]=title&rows={self.limit}&output=json&sort[]=downloads+desc"
        yield scrapy.Request(url, callback=self.parse_search, headers={"Accept": "application/json"})

    def _get_equipment_terms(self) -> str:
        """Generate search terms based on category and equipment type."""
        terms_map = {
            "hvac": {
                "furnace": "(furnace OR \"gas furnace\" OR \"oil furnace\" OR \"electric furnace\")",
                "heat_pump": "(\"heat pump\" OR heatpump OR \"air source\" OR \"ground source\")",
                "boiler": "(boiler OR \"hot water boiler\" OR \"steam boiler\")",
                "central_air": "(\"central air\" OR \"air conditioning\" OR \"ac unit\" OR condenser)",
                "mini_split": "(\"mini split\" OR \"ductless\" OR \"wall mount\")",
                "thermostat": "(thermostat OR \"smart thermostat\" OR \"programmable thermostat\")",
            },
            "solar": {
                "microinverter": "(microinverter OR \"micro inverter\" OR enphase)",
                "solar_panel": "(\"solar panel\" OR \"solar module\" OR photovoltaic OR pv)",
                "string_inverter": "(\"string inverter\" OR \"central inverter\" OR solaredge)",
                "monitoring": "(\"production monitor\" OR \"solar monitoring\" OR envoy)",
            },
            "roofing": {
                "standing_seam": "(\"standing seam\" OR \"metal roofing\" OR \"steel roofing\")",
                "shingle": "(shingle OR \"asphalt shingle\" OR \"architectural shingle\")",
                "gutter": "(gutter OR downspout OR \"gutter system\")",
            },
            "electrical": {
                "panel": "(\"electrical panel\" OR \"breaker panel\" OR \"load center\")",
                "outlet": "(outlet OR receptacle OR gfci OR afci)",
                "switch": "(\"light switch\" OR dimmer OR \"smart switch\")",
            },
            "plumbing": {
                "water_heater": "(\"water heater\" OR \"hot water heater\" OR tankless)",
                "pump": "(\"water pump\" OR \"sump pump\" OR \"sewage pump\")",
                "faucet": "(faucet OR tap OR \"kitchen faucet\" OR \"bathroom faucet\")",
            }
        }
        
        category_terms = terms_map.get(self.category, {})
        return category_terms.get(self.equipment, f"({self.equipment})")

    def parse_search(self, response: scrapy.http.Response):
        import json
        data = json.loads(response.text)
        docs = data.get("response", {}).get("docs", [])
        
        for d in docs:
            identifier = d.get("identifier")
            if not identifier:
                continue
            
            # Fetch detailed metadata
            meta_url = f"https://archive.org/metadata/{identifier}"
            yield scrapy.Request(meta_url, callback=self.parse_item, cb_kwargs={"identifier": identifier})

    def parse_item(self, response: scrapy.http.Response, identifier: str):
        import json
        meta = json.loads(response.text)
        files = meta.get("files", [])
        title = meta.get("metadata", {}).get("title") or identifier
        
        # Get largest PDF
        pdfs = [f for f in files if f.get("format", "").lower() == "text pdf" or (f.get("name", "").lower().endswith(".pdf"))]
        if not pdfs:
            return
            
        pdfs.sort(key=lambda f: f.get("size", 0) or 0, reverse=True)
        pdf = pdfs[0]
        file_url = f"https://archive.org/download/{identifier}/{pdf.get('name')}"
        
        # Infer brand from title if not specified
        brand = self.brand or self._extract_brand(title)
        model = self._extract_model(title)
        
        yield {
            "brand": brand,
            "model_number": model,
            "doc_type": "service",
            "equipment_category": self.category,
            "equipment_type": self.equipment,
            "title": title,
            "source_url": f"https://archive.org/details/{identifier}",
            "file_url": file_url,
        }

    def _extract_brand(self, title: str) -> str:
        """Extract brand from title text."""
        title_lower = title.lower()
        common_brands = ["carrier", "trane", "lennox", "rheem", "goodman", "york", "enphase", "solaredge", 
                        "kohler", "moen", "delta", "honeywell", "nest", "ring", "whirlpool", "ge", "lg", "samsung"]
        for brand in common_brands:
            if brand in title_lower:
                return brand
        return "unknown"

    def _extract_model(self, title: str) -> str:
        """Extract model number from title."""
        import re
        # Look for alphanumeric model patterns
        model_match = re.search(r'\b([A-Z0-9\-]{4,})\b', title)
        return model_match.group(1) if model_match else "unknown"
