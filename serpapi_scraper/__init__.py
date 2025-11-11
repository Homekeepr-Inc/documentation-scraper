"""
SerpApi-backed scraping utilities.

Expose a single orchestration entry point that fetches high-quality PDF
manuals via Google Search before falling back to brand-specific headless
scrapers.
"""

from .orchestrator import (
    fetch_manual_with_serpapi,
    SerpApiError,
    SerpApiConfigError,
    SerpApiQuotaError,
)

__all__ = [
    "fetch_manual_with_serpapi",
    "SerpApiError",
    "SerpApiConfigError",
    "SerpApiQuotaError",
]
