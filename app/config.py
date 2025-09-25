"""
Centralized configuration for the Home Equipment Manuals Corpus.
"""

import os
from pathlib import Path

# Storage Configuration
# Get the project root directory (parent of app directory)
PROJECT_ROOT = Path(__file__).parent.parent
DEFAULT_BLOB_ROOT = PROJECT_ROOT / "data" / "storage"
BLOB_ROOT = Path(os.environ.get("BLOB_ROOT", str(DEFAULT_BLOB_ROOT)))

DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "manuals.db"
DB_PATH = Path(os.environ.get("DB_PATH", str(DEFAULT_DB_PATH)))

# Crawler Configuration (optimized for speed)
DEFAULT_TIMEOUT = 15  # Reduced from 30s for faster failures
DOWNLOAD_TIMEOUT = int(os.environ.get("DOWNLOAD_TIMEOUT", DEFAULT_TIMEOUT))

DEFAULT_USER_AGENT = "home-equipment-crawler/1.0 (+contact: admin@local)"
USER_AGENT = os.environ.get("USER_AGENT", DEFAULT_USER_AGENT)

DEFAULT_CONCURRENT_REQUESTS = 16  # Doubled for speed
CONCURRENT_REQUESTS = int(os.environ.get("CONCURRENT_REQUESTS", DEFAULT_CONCURRENT_REQUESTS))

DEFAULT_DOWNLOAD_DELAY = 0.1  # Reduced for speed
DOWNLOAD_DELAY = float(os.environ.get("DOWNLOAD_DELAY", DEFAULT_DOWNLOAD_DELAY))

# API Configuration
DEFAULT_API_PORT = 8000
API_PORT = int(os.environ.get("API_PORT", DEFAULT_API_PORT))

# Proxy Configuration
PROXY_URL = os.environ.get("PROXY_URL")


# Internet Archive Configuration
IA_SEARCH_URL = "https://archive.org/advancedsearch.php"
IA_METADATA_URL = "https://archive.org/metadata/{identifier}"

# Supported brands and equipment
MAJOR_APPLIANCE_BRANDS = [
    "whirlpool", "ge", "lg", "samsung", "frigidaire", "bosch", 
    "maytag", "kitchenaid", "kenmore", "electrolux"
]

HVAC_BRANDS = [
    "carrier", "trane", "lennox", "rheem", "goodman", "york",
    "american_standard", "bryant", "payne"
]

SOLAR_BRANDS = [
    "enphase", "solaredge", "sma", "fronius", "abb", "huawei", "generac"
]

DOCUMENT_TYPES = [
    "owner", "service", "installation", "tech_sheet", "wiring", "spec"
]

EQUIPMENT_CATEGORIES = [
    "appliance", "hvac", "solar", "electrical", "plumbing", "roofing", "security", "outdoor"
]

# Validation
def validate_brand(brand: str) -> str:
    """Validate and normalize brand name."""
    brand_lower = brand.lower()
    all_brands = MAJOR_APPLIANCE_BRANDS + HVAC_BRANDS + SOLAR_BRANDS
    if brand_lower not in all_brands:
        print(f"⚠️  Warning: '{brand}' not in known brands. Proceeding anyway.")
    return brand_lower

def validate_doc_type(doc_type: str) -> str:
    """Validate and normalize document type."""
    doc_type_lower = doc_type.lower()
    if doc_type_lower not in DOCUMENT_TYPES:
        print(f"⚠️  Warning: '{doc_type}' not in known types: {DOCUMENT_TYPES}")
    return doc_type_lower

def validate_equipment_category(category: str) -> str:
    """Validate and normalize equipment category."""
    category_lower = category.lower()
    if category_lower not in EQUIPMENT_CATEGORIES:
        print(f"⚠️  Warning: '{category}' not in known categories: {EQUIPMENT_CATEGORIES}")
    return category_lower
