"""
Headless scraper for retrieving manuals from SearsPartsDirect.

The flow mirrors the Manualslib scraper but is far simpler:
    1. Load the SearsPartsDirect product/manual page.
    2. Locate the download guide section and its anchor.
    3. Click the anchor so Chrome downloads the PDF into the provided directory.
"""

from __future__ import annotations

import contextlib
import logging
import os
import sys
import time
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urljoin, urlparse

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
    TimeoutException,
)
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
    wait_for_download,
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


def _is_probable_pdf(url: str) -> bool:
    cleaned = (url or "").lower().split("?", 1)[0]
    return cleaned.endswith(".pdf")


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
    return not _is_probable_pdf(path)


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
        if download_attr or "download" in text or href.lower().endswith(".pdf"):
            return anchor
    return anchors[0] if anchors else None


def _click_anchor(driver, anchor) -> bool:
    """Attempt to click an anchor, scrolling it into view first."""

    for attempt in range(1, 4):
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", anchor)
            time.sleep(0.3)
            anchor.click()
            return True
        except (ElementClickInterceptedException, ElementNotInteractableException) as exc:
            logger.debug("Attempt %s to click SearsPartsDirect anchor failed: %s", attempt, exc)
            time.sleep(0.4)

    try:
        driver.execute_script("arguments[0].click();", anchor)
        logger.debug("Clicked SearsPartsDirect anchor via JS fallback")
        return True
    except Exception as exc:  # pylint: disable=broad-except
        logger.warning("Failed to click SearsPartsDirect anchor via JS fallback: %s", exc)
        return False


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
    initial_snapshot = set(os.listdir(download_dir))

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

        if not _click_anchor(driver, anchor):
            logger.info("Unable to click SearsPartsDirect download link url=%s", normalized_url)
            return None

        pdf_path = wait_for_download(
            download_dir,
            timeout=download_timeout,
            initial_files=initial_snapshot,
            expected_extensions=(".pdf",),
            logger=lambda message: logger.debug("SearsPartsDirect download: %s", message),
        )
        if not pdf_path:
            logger.info("SearsPartsDirect download timed out url=%s", normalized_url)
            return None

        return SearsPartsDirectDownload(
            product_url=normalized_url,
            download_url=download_url,
            pdf_path=pdf_path,
        )
    finally:
        with contextlib.suppress(Exception):
            driver.quit()
