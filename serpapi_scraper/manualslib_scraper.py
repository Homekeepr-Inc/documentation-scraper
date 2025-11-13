"""
Headless scraper for retrieving manuals from ManualsLib.

This module focuses on the happy path needed by the SerpApi orchestrator:
    1. Load the ManualsLib product search result page.
    2. Follow the first manual link in the results list.
    3. Resolve the download button on the manual detail page.
    4. Navigate directly to the download URL so the PDF is saved locally.
"""

from __future__ import annotations

import logging
import os
import sys
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urljoin, urlparse

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Reuse shared headless utilities for driver management and download handling.
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

import time

from .ai_captcha_bridge import detect_recaptcha, solve_recaptcha_if_present

logger = logging.getLogger("serpapi.manualslib")

PRODUCT_PATH_PREFIX = "/products/"
MANUAL_LINK_SELECTOR = "h3.search_h3 a[href*='/manual/']"
DOWNLOAD_BUTTON_SELECTOR = "a#download-manual-btn.btn__download-manual"


@dataclass
class ManualslibDownload:
    """Represents the resolved ManualsLib artifact for a single manual."""

    product_url: str
    manual_page_url: str
    download_url: str
    pdf_path: str


def is_manualslib_product_url(url: str) -> bool:
    """Check whether the URL points to a ManualsLib product listing."""

    if not url:
        return False
    try:
        parsed = urlparse(url)
    except Exception:  # pylint: disable=broad-except
        return False

    host = (parsed.netloc or "").lower()
    if not host.endswith("manualslib.com"):
        return False

    path = parsed.path or ""
    return path.startswith(PRODUCT_PATH_PREFIX)


def _wait_for_manual_link(driver, timeout: int) -> Optional[str]:
    """Return the first manual link discovered on the product page."""

    wait = WebDriverWait(driver, timeout)
    try:
        elements = wait.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, MANUAL_LINK_SELECTOR))
        )
    except TimeoutException:
        logger.info("Manual link not found within timeout on ManualsLib product page")
        return None

    for element in elements:
        href = element.get_attribute("href") or ""
        if href:
            return href
    return None


def _resolve_download_link(driver, timeout: int) -> Optional[str]:
    """Extract the download link from the manual detail page."""

    wait = WebDriverWait(driver, timeout)
    try:
        element = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, DOWNLOAD_BUTTON_SELECTOR))
        )
    except TimeoutException:
        logger.info("Download button not found within timeout on ManualsLib manual page")
        return None

    href = element.get_attribute("href") or ""
    return href or None


def _handle_captcha(
    driver,
    *,
    click_get_manual: bool = True,
    context: str = "manualslib",
) -> bool:
    """
    Detect and solve any reCAPTCHA challenge surfaced on the current page.

    Returns True when no CAPTCHA is present or after a successful solve.
    """

    logger.debug("(%s) Checking for reCAPTCHA challenge", context)
    if not detect_recaptcha(driver):
        logger.debug("(%s) No reCAPTCHA iframe detected", context)
        return True

    solved = solve_recaptcha_if_present(driver, context=context, logger=logger)
    if not solved:
        logger.warning("(%s) Failed to solve reCAPTCHA challenge", context)
        return False
    logger.info("(%s) Successfully solved reCAPTCHA challenge", context)

    if not click_get_manual:
        return True

    try:
        get_manual_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "get-manual-button"))
        )
        get_manual_button.click()
        logger.info("(%s) Clicked 'Get manual' button after CAPTCHA solve", context)
        time.sleep(2)
        if not solve_recaptcha_if_present(
            driver,
            context=f"{context}:post-get-manual",
            logger=logger,
        ):
            logger.warning("(%s) Additional reCAPTCHA after 'Get manual' click failed", context)
            return False
    except TimeoutException:
        logger.warning("(%s) Could not find or click 'Get manual' button after CAPTCHA", context)
        return False

    logger.debug("(%s) CAPTCHA handling complete", context)
    return True


def download_manual_from_product_page(
    product_url: str,
    *,
    download_dir: str,
    navigation_timeout: int = 25,
    download_timeout: int = 45,
) -> Optional[ManualslibDownload]:
    """
    Navigate a ManualsLib product URL and download the linked manual PDF.

    Returns a ManualslibDownload on success, otherwise None.
    """

    if not is_manualslib_product_url(product_url):
        logger.debug("Skipping ManualsLib navigation for non-product URL %s", product_url)
        return None

    if not product_url.lower().startswith(("http://", "https://")):
        product_url = f"https://{product_url.lstrip('/')}"

    os.makedirs(download_dir, exist_ok=True)
    initial_snapshot = set(os.listdir(download_dir))

    chrome_options = get_chrome_options(download_dir=download_dir)
    driver = create_chrome_driver(options=chrome_options, download_dir=download_dir)

    try:
        logger.info("Navigating ManualsLib product page url=%s", product_url)
        safe_driver_get(driver, product_url, timeout=navigation_timeout)

        manual_href = _wait_for_manual_link(driver, navigation_timeout)
        if not manual_href:
            return None

        manual_url = urljoin(product_url, manual_href)
        logger.info("Navigating ManualsLib manual page url=%s", manual_url)
        safe_driver_get(driver, manual_url, timeout=navigation_timeout)

        wait = WebDriverWait(driver, navigation_timeout)
        try:
            download_button = wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, DOWNLOAD_BUTTON_SELECTOR))
            )
            download_href = download_button.get_attribute("href") or ""
            download_url = urljoin(manual_url, download_href)
            if not _handle_captcha(driver, click_get_manual=False, context="pre-download click"):
                logger.warning("Aborting ManualsLib scrape due to CAPTCHA failure before download click")
                return None
            logger.info("Clicking ManualsLib download button for url=%s", download_url)
            download_button.click()
            time.sleep(3)  # Wait for CAPTCHA page to load

            if not _handle_captcha(driver, context="post-download click"):
                logger.warning("Aborting ManualsLib scrape due to CAPTCHA failure after download click")
                return None
        except TimeoutException:
            logger.info("Download button not found within timeout on ManualsLib manual page")
            return None

        pdf_path = wait_for_download(
            download_dir,
            timeout=download_timeout,
            initial_files=initial_snapshot,
            expected_extensions=(".pdf",),
            logger=lambda message: logger.debug("ManualsLib download: %s", message),
        )
        if not pdf_path:
            logger.info("ManualsLib download did not complete within timeout")
            return None

        return ManualslibDownload(
            product_url=product_url,
            manual_page_url=manual_url,
            download_url=download_url,
            pdf_path=pdf_path,
        )
    finally:
        try:
            driver.quit()
        except Exception:  # pylint: disable=broad-except
            pass
