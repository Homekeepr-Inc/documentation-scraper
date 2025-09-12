from typing import Any, Dict

from app.ingest import ingest_from_url


class IngestPipeline:
    def process_item(self, item: Dict[str, Any], spider):
        brand = item.get("brand")
        model_number = item.get("model_number") or "unknown"
        doc_type = item.get("doc_type") or "service"
        title = item.get("title") or "manual"
        source_url = item.get("source_url") or item.get("landing_url") or item.get("file_url")
        file_url = item.get("file_url")
        equipment_category = item.get("equipment_category") or "appliance"
        equipment_type = item.get("equipment_type") or "unknown"
        
        if not (brand and file_url):
            return item
        res = ingest_from_url(
            brand=brand,
            model_number=model_number,
            doc_type=doc_type,
            title=title,
            source_url=source_url or file_url,
            file_url=file_url,
            equipment_category=equipment_category,
            equipment_type=equipment_type,
        )
        item["ingested"] = True
        item["ingest_id"] = res.id
        item["sha256"] = res.sha256
        return item
