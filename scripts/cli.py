#!/usr/bin/env python3
"""
Simple CLI for Home Equipment Manuals Corpus
Usage: python3 scripts/simple_cli.py <command> [args]
"""

import sys
import time
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from app import db
from app.ingest import ingest_from_url
from app.config import validate_brand, validate_doc_type, MAJOR_APPLIANCE_BRANDS, DOCUMENT_TYPES
from app.logging_config import setup_logging, get_logger
import requests
import json

# Setup logging
setup_logging()
logger = get_logger("cli")


def init_db():
    """Initialize the database."""
    db.init_db()
    print("✅ Database initialized")


def stats():
    """Show corpus statistics."""
    conn = db.get_db()
    try:
        total = conn.execute('SELECT COUNT(*) FROM documents').fetchone()[0]
        print(f"📊 Total documents: {total}")
        
        if total > 0:
            brands = conn.execute('SELECT brand, COUNT(*) FROM documents GROUP BY brand ORDER BY COUNT(*) DESC').fetchall()
            print("\n📈 By brand:")
            for brand, count in brands:
                print(f"  {brand}: {count}")
            
            categories = conn.execute('SELECT equipment_category, COUNT(*) FROM documents GROUP BY equipment_category').fetchall()
            if categories:
                print("\n🏠 By equipment category:")
                for cat, count in categories:
                    print(f"  {cat}: {count}")
    finally:
        conn.close()


def crawl_ia(brand="whirlpool", rows=50):
    """Crawl Internet Archive for a brand."""
    # Validate inputs
    brand = validate_brand(brand)
    if rows <= 0 or rows > 1000:
        print(f"⚠️  Warning: rows={rows} outside recommended range (1-1000)")
        
    db.init_db()
    logger.info(f"Starting IA crawl: {brand} ({rows} max)")
    print(f"📥 Crawling Internet Archive: {brand} ({rows} max)")
    
    # Simplified IA query
    query = f'collection:manuals AND {brand} AND (manual OR service OR installation)'
    params = {
        "q": query,
        "fl[]": ["identifier", "title"],
        "rows": rows,
        "output": "json",
    }
    
    r = requests.get("https://archive.org/advancedsearch.php", params=params, timeout=60)
    r.raise_for_status()
    docs = r.json().get("response", {}).get("docs", [])
    
    # Speed optimization: Batch process identifiers
    valid_identifiers = []
    for d in docs:
        identifier = d.get("identifier")
        if identifier and brand.lower() in identifier.lower():
            valid_identifiers.append(identifier)
    
    logger.info(f"Processing {len(valid_identifiers)} valid identifiers")
    
    count = 0
    for identifier in valid_identifiers:
        # Get metadata with reduced timeout
        meta_url = f"https://archive.org/metadata/{identifier}"
        try:
            meta = requests.get(meta_url, timeout=10).json()  # Reduced timeout
        except requests.RequestException as e:
            logger.warning(f"Metadata fetch failed for {identifier}: {e}")
            continue
            
        files = meta.get("files", [])
        title = meta.get("metadata", {}).get("title") or identifier
        
        # Find largest PDF
        pdfs = [f for f in files if f.get("name", "").lower().endswith(".pdf")]
        if not pdfs:
            continue
        pdf = max(pdfs, key=lambda f: f.get("size", 0) or 0)
        file_url = f"https://archive.org/download/{identifier}/{pdf.get('name')}"
        
        try:
            result = ingest_from_url(
                brand=brand,
                model_number="unknown",
                doc_type="service",
                title=title,
                source_url=f"https://archive.org/details/{identifier}",
                file_url=file_url,
                equipment_category="appliance",
                equipment_type="unknown",
            )
            if result.id:  # Only count new ingestions
                count += 1
                print(f"✅ {identifier}")
            else:
                print(f"⏭️  {identifier} (duplicate)")
        except Exception as e:
            logger.error(f"Ingestion failed for {identifier}: {e}")
            print(f"❌ {identifier}: {e}")
    
    print(f"📊 Ingested {count} documents")


def bulk_crawl():
    """Large-scale crawl across multiple brands."""
    brands = ["whirlpool", "ge", "lg", "samsung", "frigidaire", "bosch"]
    print(f"🚀 Starting bulk crawl: {len(brands)} brands")
    
    for brand in brands:
        print(f"\n📥 Crawling {brand}...")
        crawl_ia(brand, 100)
    
    print("\n✅ Bulk crawl complete!")
    stats()


def crawl_sitemaps():
    """Crawl brand sitemaps for direct PDF access."""
    import os
    import subprocess
    
    brands = ["ge", "whirlpool", "lg", "samsung"]
    print(f"🗺️ Starting sitemap crawl: {len(brands)} brands")
    
    for brand in brands:
        print(f"\n📥 Sitemap crawling {brand}...")
        env = os.environ.copy()
        env["PYTHONPATH"] = "."
        cmd = [
            "python3", "-m", "scrapy", "crawl", "sitemap",
            "-a", f"brand={brand}",
            "-a", "limit=50",
            "-s", "LOG_LEVEL=INFO"
        ]
        try:
            subprocess.run(cmd, cwd="crawler", env=env, check=False, timeout=120)
        except subprocess.TimeoutExpired:
            print(f"⏱️ {brand} sitemap crawl timed out")
        except Exception as e:
            print(f"❌ {brand} sitemap error: {e}")
    
    print("\n✅ Sitemap crawl complete!")
    stats()


def crawl_ge_headless(models="CFE28TSHFSS"):
    """Crawl GE appliance parts using headless browser scraper."""
    import os
    import subprocess

    model_list = [m.strip() for m in models.split(',')]

    for model in model_list:
        print(f"🌐 Starting headless GE scrape for model: {model}")

        env = os.environ.copy()
        env["PYTHONPATH"] = "."
        cmd = [
            "python3", "headless-browser-scraper/ge_headless_scraper.py", model
        ]
        try:
            subprocess.run(cmd, env=env, check=False, timeout=300)  # 5 min timeout
        except subprocess.TimeoutExpired:
            print(f"⏱️ Headless GE scrape for {model} timed out")
        except Exception as e:
            print(f"❌ Headless GE scrape for {model} error: {e}")

    print("\n✅ Headless GE scrape complete!")
    stats()


def crawl_kitchenaid_headless(models="KOES530PSS"):
    """Crawl Kitchenaid appliance manuals using headless browser scraper."""
    import os
    import subprocess

    model_list = [m.strip() for m in models.split(',')]

    for model in model_list:
        print(f"🌐 Starting headless Kitchenaid scrape for model: {model}")

        env = os.environ.copy()
        env["PYTHONPATH"] = "."
        cmd = [
            "python3", "headless-browser-scraper/kitchenaid_headless_scraper.py", model
        ]
        try:
            subprocess.run(cmd, env=env, check=False, timeout=300)  # 5 min timeout
        except subprocess.TimeoutExpired:
            print(f"⏱️ Headless Kitchenaid scrape for {model} timed out")
        except Exception as e:
            print(f"❌ Headless Kitchenaid scrape for {model} error: {e}")

    print("\n✅ Headless Kitchenaid scrape complete!")
    stats()


def crawl_targeted_doc_type(brand="whirlpool", doc_type="tech_sheet", limit=25):
    """Crawl IA for specific document types (installation, tech_sheet, wiring, spec)."""
    # Validate inputs
    brand = validate_brand(brand)
    doc_type = validate_doc_type(doc_type)
    if limit <= 0 or limit > 100:
        print(f"⚠️  Warning: limit={limit} outside recommended range (1-100)")
        
    db.init_db()
    logger.info(f"Starting targeted crawl: {brand} {doc_type} ({limit} max)")
    
    # Document-type specific queries
    doc_queries = {
        "installation": f'{brand} AND (installation OR install OR "installation manual" OR "install guide")',
        "tech_sheet": f'{brand} AND ("tech sheet" OR "technical sheet" OR specification OR specs)',
        "wiring": f'{brand} AND (wiring OR "wiring diagram" OR schematic OR electrical)',
        "service": f'{brand} AND (service OR repair OR troubleshooting OR diagnostic)',
        "owner": f'{brand} AND ("owner manual" OR "user manual" OR "operator manual")',
    }
    
    query = f'collection:manuals AND ({doc_queries.get(doc_type, doc_queries["service"])})'
    print(f"🎯 Crawling {brand} {doc_type} documents...")
    
    params = {
        "q": query,
        "fl[]": ["identifier", "title"],
        "rows": limit,
        "output": "json",
        "sort[]": "downloads desc",
    }
    
    r = requests.get("https://archive.org/advancedsearch.php", params=params, timeout=60)
    r.raise_for_status()
    docs = r.json().get("response", {}).get("docs", [])
    
    count = 0
    for d in docs:
        identifier = d.get("identifier")
        title = (d.get("title") or "").lower()
        if not identifier or brand.lower() not in (title + " " + identifier.lower()):
            continue
            
        # Get metadata and PDF
        meta = requests.get(f"https://archive.org/metadata/{identifier}", timeout=60).json()
        files = meta.get("files", [])
        display_title = meta.get("metadata", {}).get("title") or identifier
        
        pdfs = [f for f in files if f.get("name", "").lower().endswith(".pdf")]
        if not pdfs:
            continue
        pdf = max(pdfs, key=lambda f: f.get("size", 0) or 0)
        file_url = f"https://archive.org/download/{identifier}/{pdf.get('name')}"
        
        try:
            ingest_from_url(
                brand=brand,
                model_number="unknown",
                doc_type=doc_type,
                title=display_title,
                source_url=f"https://archive.org/details/{identifier}",
                file_url=file_url,
                equipment_category="appliance",
                equipment_type="unknown",
            )
            count += 1
            print(f"✅ {doc_type}: {identifier}")
        except Exception as e:
            print(f"❌ {identifier}: {e}")
    
    print(f"📊 Ingested {count} {doc_type} documents for {brand}")


def max_scale_crawl():
    """Run ALL available crawlers for maximum dataset coverage."""
    db.init_db()
    
    print("🚀 MAXIMUM SCALE CRAWL - Loading largest possible dataset")
    print("This will run all working crawlers and strategies")
    print()
    
    start_time = time.time()
    
    # 1. Bulk brand crawl (appliances)
    print("📥 Phase 1: Multi-brand appliance crawl...")
    bulk_crawl()
    
    print("\n📥 Phase 2: Targeted document types...")
    # 2. Document type diversification
    brands = ["whirlpool", "ge", "lg", "samsung", "frigidaire", "bosch"]
    doc_types = ["installation", "tech_sheet", "wiring", "service", "owner"]
    
    for brand in brands[:3]:  # Top 3 brands for time
        for doc_type in doc_types:
            try:
                print(f"  🎯 {brand} {doc_type}...")
                crawl_targeted_doc_type(brand, doc_type, 20)  # Smaller batches for variety
            except Exception as e:
                logger.error(f"Targeted crawl failed: {brand} {doc_type}: {e}")
    
    print("\n📥 Phase 3: Brand sitemaps...")
    # 3. Sitemap crawling
    crawl_sitemaps()
    
    print("\n📥 Phase 4: Equipment categories (HVAC, solar, electrical)...")
    # 4. Equipment-specific crawling with broader IA collections
    equipment_searches = [
        ("hvac", "furnace", "carrier"),
        ("hvac", "heat_pump", "trane"), 
        ("solar", "inverter", "enphase"),
        ("electrical", "panel", "siemens"),
        ("plumbing", "water_heater", "rheem"),
    ]
    
    for category, equipment, brand in equipment_searches:
        try:
            print(f"  🏠 {category}/{equipment} ({brand})...")
            crawl_equipment_broad(category, equipment, brand)
        except Exception as e:
            logger.error(f"Equipment crawl failed: {category}/{equipment}: {e}")
    
    # Final statistics
    elapsed = time.time() - start_time
    print(f"\n🎉 MAX-SCALE CRAWL COMPLETE!")
    print(f"⏱️  Total time: {elapsed/60:.1f} minutes")
    print()
    stats()
    print()
    print("🌐 Browse your comprehensive dataset: http://localhost:8000")


def crawl_equipment_broad(category, equipment, brand, limit=30):
    """Broader equipment crawling across multiple IA collections."""
    # Expand beyond just "manuals" collection
    collections = ["manuals", "texts", "documents"]
    
    for collection in collections:
        query = f'collection:{collection} AND {brand} AND {equipment} AND (manual OR guide OR installation OR service)'
        params = {
            "q": query,
            "fl[]": ["identifier", "title"],
            "rows": limit // len(collections),  # Split limit across collections
            "output": "json",
        }
        
        try:
            r = requests.get("https://archive.org/advancedsearch.php", params=params, timeout=10)
            r.raise_for_status()
            docs = r.json().get("response", {}).get("docs", [])
            
            for d in docs:
                identifier = d.get("identifier")
                if not identifier:
                    continue
                    
                # Quick metadata fetch
                meta = requests.get(f"https://archive.org/metadata/{identifier}", timeout=5).json()
                files = meta.get("files", [])
                title = meta.get("metadata", {}).get("title") or identifier
                
                pdfs = [f for f in files if f.get("name", "").lower().endswith(".pdf")]
                if not pdfs:
                    continue
                pdf = max(pdfs, key=lambda f: f.get("size", 0) or 0)
                file_url = f"https://archive.org/download/{identifier}/{pdf.get('name')}"
                
                try:
                    ingest_from_url(
                        brand=brand,
                        model_number="unknown",
                        doc_type="service",
                        title=title,
                        source_url=f"https://archive.org/details/{identifier}",
                        file_url=file_url,
                        equipment_category=category,
                        equipment_type=equipment,
                    )
                    print(f"    ✅ {identifier}")
                except Exception:
                    continue
                    
        except Exception as e:
            logger.warning(f"Collection {collection} failed for {category}/{equipment}: {e}")


def setup():
    """Quick setup with sample data."""
    print("🚀 Setting up Home Equipment Manuals Corpus...")
    init_db()
    print("🔧 Loading sample data...")
    crawl_ia("whirlpool", 5)
    print("\n🎉 Setup complete!")
    print("Start web UI: export PYTHONPATH=. && python3 -m uvicorn app.main:app --reload")
    print("Browse at: http://localhost:8000")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 scripts/cli.py <command>")
        print("\nCommands:")
        print("  setup          - Initialize and load sample data")
        print("  init           - Initialize database")
        print("  stats          - Show corpus statistics") 
        print("  crawl-ia       - Crawl Internet Archive (brand, rows)")
        print("  bulk           - Large-scale multi-brand crawl")
        print("  sitemaps       - Crawl brand sitemaps for direct PDF access")
        print("  headless-ge    - Crawl GE using headless browser (model)")
        print("  headless-kitchenaid - Crawl Kitchenaid using headless browser (model)")
        print("  targeted       - Targeted document type crawling")
        print("  max-scale      - Run ALL crawlers for maximum dataset (recommended)")
        print("\nExamples:")
        print("  python3 scripts/cli.py setup")
        print("  python3 scripts/cli.py max-scale")
        print("  python3 scripts/cli.py crawl-ia samsung 50")
        print("  python3 scripts/cli.py targeted whirlpool tech_sheet")
        print("  python3 scripts/cli.py headless-ge CFE28TSHFSS")
        print("  python3 scripts/cli.py headless-kitchenaid KOES530PSS")
        return
    
    cmd = sys.argv[1]
    
    if cmd == "setup":
        setup()
    elif cmd == "init":
        init_db()
    elif cmd == "stats":
        stats()
    elif cmd == "crawl-ia":
        brand = sys.argv[2] if len(sys.argv) > 2 else "whirlpool"
        rows = int(sys.argv[3]) if len(sys.argv) > 3 else 50
        crawl_ia(brand, rows)
    elif cmd == "bulk":
        bulk_crawl()
    elif cmd == "sitemaps":
        crawl_sitemaps()
    elif cmd == "headless-ge":
        models = sys.argv[2] if len(sys.argv) > 2 else "CFE28TSHFSS"
        crawl_ge_headless(models)
    elif cmd == "headless-kitchenaid":
        models = sys.argv[2] if len(sys.argv) > 2 else "KOES530PSS"
        crawl_kitchenaid_headless(models)
    elif cmd == "targeted":
        brand = sys.argv[2] if len(sys.argv) > 2 else "whirlpool"
        doc_type = sys.argv[3] if len(sys.argv) > 3 else "tech_sheet"
        crawl_targeted_doc_type(brand, doc_type)
    elif cmd == "max-scale":
        max_scale_crawl()
    else:
        print(f"Unknown command: {cmd}")
        print("Run 'python3 scripts/cli.py' to see available commands")


if __name__ == "__main__":
    main()
