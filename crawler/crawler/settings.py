BOT_NAME = "crawler"

SPIDER_MODULES = ["crawler.spiders"]
NEWSPIDER_MODULE = "crawler.spiders"

ROBOTSTXT_OBEY = True
CONCURRENT_REQUESTS = 16  # Increased for speed
DOWNLOAD_DELAY = 0.1      # Reduced delay
USER_AGENT = "home-equipment-crawler/1.0 (+contact: admin@local)"
DOWNLOAD_TIMEOUT = 15     # Faster failures
RETRY_TIMES = 2
RETRY_HTTP_CODES = [429, 500, 502, 503, 504]

# Ensure project root is importable so pipelines can import app.ingest
import os, sys
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# Ensure crawler runs from project root for consistent database paths
os.chdir(PROJECT_ROOT)

# Proxy configuration
from app.config import PROXY_URL
if PROXY_URL:
    HTTP_PROXY = PROXY_URL
    HTTPS_PROXY = PROXY_URL

# Standard HTTP handlers (Playwright removed for simplicity)
# Note: Playwright can be re-added if needed for JS-heavy sites

ITEM_PIPELINES = {
    "crawler.pipelines.IngestPipeline": 300,
}
