"""
Headless scraper for retrieving manuals from SearsPartsDirect.

The flow mirrors the Manualslib scraper but is far simpler:
    1. Load the SearsPartsDirect product/manual page.
    2. Locate the download guide section and its anchor.
    3. Resolve the anchor href and download the PDF via requests.
"""

from __future__ import annotations

import contextlib
import logging
import os
import sys
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urljoin, urlparse

import requests
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Reuse the shared headless utils (driver + download handling).
HEADLESS_UTILS_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "headless-browser-scraper")
)
if HEADLESS_UTILS_PATH not in sys.path:
    sys.path.append(HEADLESS_UTILS_PATH)

from utils import (  # type: ignore  # pylint: disable=import-error
    create_chrome_driver,
    get_chrome_options,
    safe_driver_get,
)

logger = logging.getLogger("serpapi.searspartsdirect")

DOWNLOAD_LINK_SELECTOR = "div.download-guide a"
DEFAULT_NAVIGATION_TIMEOUT = 20
DEFAULT_DOWNLOAD_TIMEOUT = 45


@dataclass
class SearsPartsDirectDownload:
    """Represents a resolved SearsPartsDirect manual artifact."""

    product_url: str
    download_url: str
    pdf_path: str


def is_searspartsdirect_manual_page(url: str) -> bool:
    """Return True when the URL is an HTML SearsPartsDirect manual/product page."""

    if not url:
        return False
    try:
        parsed = urlparse(url)
    except Exception:  # pylint: disable=broad-except
        return False
    host = (parsed.netloc or "").lower()
    if not host.endswith("searspartsdirect.com"):
        return False
    path = (parsed.path or "").lower()
    return not path.endswith(".pdf")


def _select_download_anchor(driver, timeout: int):
    """Find the most likely download link inside the download-guide block."""

    wait = WebDriverWait(driver, timeout)
    try:
        anchors = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, DOWNLOAD_LINK_SELECTOR))
        )
    except TimeoutException:
        logger.info("SearsPartsDirect download section not found before timeout")
        return None

    for anchor in anchors:
        href = (anchor.get_attribute("href") or "").strip()
        if not href:
            continue
        download_attr = (anchor.get_attribute("download") or "").strip()
        text = (anchor.text or "").strip().lower()
        if download_attr or "download" in text:
            return anchor
    return anchors[0] if anchors else None


def _download_pdf_to_dir(download_url: str, download_dir: str, filename_hint: str, timeout: int) -> Optional[str]:
    """Download the PDF with requests into the provided directory."""

    filename = filename_hint or "searspartsdirect-manual.pdf"
    if not filename.lower().endswith(".pdf"):
        filename = f"{filename}.pdf"

    target_path = os.path.join(download_dir, filename)
    base, ext = os.path.splitext(target_path)
    counter = 1
    while os.path.exists(target_path):
        target_path = f"{base}-{counter}{ext or '.pdf'}"
        counter += 1

    logger.info("Downloading SearsPartsDirect PDF directly url=%s path=%s", download_url, target_path)
    try:
        response = requests.get(download_url, timeout=timeout, stream=True)
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.info("SearsPartsDirect PDF request failed url=%s error=%s", download_url, exc)
        return None

    try:
        with open(target_path, "wb") as pdf_file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    pdf_file.write(chunk)
    except OSError as exc:
        logger.info("SearsPartsDirect file write failed path=%s error=%s", target_path, exc)
        return None

    return target_path


def download_manual_from_product_page(
    product_url: str,
    *,
    download_dir: str,
    navigation_timeout: int = DEFAULT_NAVIGATION_TIMEOUT,
    download_timeout: int = DEFAULT_DOWNLOAD_TIMEOUT,
) -> Optional[SearsPartsDirectDownload]:
    """Load a SearsPartsDirect page and download the associated manual PDF."""

    if not is_searspartsdirect_manual_page(product_url):
        logger.debug("Skipping SearsPartsDirect scrape for non-product url=%s", product_url)
        return None

    normalized_url = product_url
    if not normalized_url.lower().startswith(("http://", "https://")):
        normalized_url = f"https://{normalized_url.lstrip('/')}"

    os.makedirs(download_dir, exist_ok=True)

    chrome_options = get_chrome_options(download_dir=download_dir)
    driver = create_chrome_driver(options=chrome_options, download_dir=download_dir)

    try:
        logger.info("Navigating SearsPartsDirect page url=%s", normalized_url)
        safe_driver_get(driver, normalized_url, timeout=navigation_timeout)

        anchor = _select_download_anchor(driver, navigation_timeout)
        if not anchor:
            logger.info("SearsPartsDirect download link not found url=%s", normalized_url)
            return None

        raw_href = anchor.get_attribute("href") or ""
        download_url = urljoin(normalized_url, raw_href)

        filename_hint = os.path.basename(urlparse(download_url).path) or "searspartsdirect-manual.pdf"
        pdf_path = _download_pdf_to_dir(download_url, download_dir, filename_hint, download_timeout)
        if not pdf_path:
            logger.info("SearsPartsDirect PDF download failed url=%s download_url=%s", normalized_url, download_url)
            return None

        return SearsPartsDirectDownload(
            product_url=normalized_url,
            download_url=download_url,
            pdf_path=pdf_path,
        )
    finally:
        with contextlib.suppress(Exception):
            driver.quit()
