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
from typing import Any, Dict, Optional
from urllib.parse import urljoin, urlparse

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
    TimeoutException,
)
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
# THe download button on the page before the actual download. ManualsLib is annoying.
PRE_DOWNLOAD_BUTTON_SELECTOR = "download-manual-btn"
DOWNLOAD_BUTTON_SELECTOR = "get-manual-button"
DOWNLOAD_LINK_SELECTOR = "a.download-url"
VIEW_LINK_SELECTOR = "a.view-url"

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
            EC.presence_of_element_located((By.ID, PRE_DOWNLOAD_BUTTON_SELECTOR))
        )
    except TimeoutException:
        logger.info("Download button not found within timeout on ManualsLib manual page")
        return None

    href = element.get_attribute("href") or ""
    return href or None


def _click_element_with_fallback(
    driver,
    element,
    *,
    description: str,
    logger: logging.Logger,
    attempts: int = 3,
) -> bool:
    """
    Try to click an element, scrolling it into view and falling back to JS clicks.
    """

    for attempt in range(1, attempts + 1):
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.4)
            element.click()
            return True
        except (ElementClickInterceptedException, ElementNotInteractableException) as exc:
            logger.debug(
                "Attempt %d to click %s failed: %s",
                attempt,
                description,
                exc,
            )
            driver.execute_script("window.scrollBy(0, -120);")
            time.sleep(0.6)

    try:
        driver.execute_script("arguments[0].click();", element)
        logger.debug("Clicked %s via JS fallback", description)
        return True
    except Exception as exc:  # pylint: disable=broad-except
        logger.warning("Could not click %s via JS fallback: %s", description, exc)
        return False


def _submit_ajax_get_manual_request(
    driver,
    *,
    context: str,
    logger: logging.Logger,
) -> Optional[Dict[str, Any]]:
    """
    Attempt to fire the same AJAX request ManualsLib uses after clicking the button.
    """

    script = """
const callback = arguments[0];
try {
    const block = document.getElementById('dl_captcha');
    if (!block) {
        callback({ok: false, error: 'captcha_block_missing'});
        return;
    }
    const captchaInput = block.querySelector('[name="g-recaptcha-response"]');
    const idInput = block.querySelector('[name="id"]');
    const payload = {
        captcha: captchaInput ? captchaInput.value : '',
        id: idInput ? idInput.value : '',
        f_hash: window.f_hash || null,
        var1: window.screen ? window.screen.availWidth : null,
        var2: window.screen ? window.screen.availHeight : null,
        var3: document.referrer || ''
    };
    const jq = window.jQuery || window.$;
    if (!jq || !jq.post) {
        callback({ok: false, error: 'jquery_missing'});
        return;
    }
    jq.post('/download', payload)
        .done(function(resp) {
            window.__manualslibDownloadResponse = resp || {};
            callback({ok: true, resp: resp || {}});
        })
        .fail(function(jqXHR, textStatus, errorThrown) {
            callback({
                ok: false,
                error: (errorThrown || textStatus || 'request_failed'),
                status: jqXHR && jqXHR.status
            });
        });
} catch (err) {
    callback({ok: false, error: err && err.message ? err.message : String(err)});
}
    """
    try:
        result = driver.execute_async_script(script)
    except Exception as exc:  # pylint: disable=broad-except
        logger.debug("(%s) AJAX 'Get manual' script execution failed: %s", context, exc)
        return None

    if not isinstance(result, dict):
        logger.debug("(%s) Unexpected AJAX response type: %s", context, result)
        return None

    if result.get("ok"):
        resp = result.get("resp") or {}
        if isinstance(resp, dict):
            try:
                driver.execute_script("window.__manualslibDownloadResponse = arguments[0] || {};", resp)
            except Exception:  # pylint: disable=broad-except
                pass
            return resp

    logger.warning(
        "(%s) AJAX download request failed: %s",
        context,
        result.get("error") or "unknown error",
    )
    return None


def _get_cached_ajax_download_response(driver) -> Optional[Dict[str, Any]]:
    """Return the cached AJAX response set on the window, if any."""

    try:
        response = driver.execute_script("return window.__manualslibDownloadResponse || null;")
    except Exception:  # pylint: disable=broad-except
        return None
    return response if isinstance(response, dict) else None


def _navigate_via_cached_response(
    driver,
    response: Dict[str, Any],
    *,
    context: str,
    logger: logging.Logger,
) -> bool:
    """Navigate directly to the download URL captured from the AJAX response."""

    direct_url = response.get("url") or response.get("customPdfPath")
    if not isinstance(direct_url, str) or not direct_url:
        return False

    if response.get("url"):
        download_target = f"{direct_url}&take=binary"
    else:
        download_target = f"{direct_url}?take=binary"

    if download_target.startswith("//"):
        download_target = f"https:{download_target}"

    logger.info("(%s) Navigating directly to download url=%s", context, download_target)
    try:
        driver.get(download_target)
    except Exception as exc:  # pylint: disable=broad-except
        logger.warning(
            "(%s) Direct navigation to download URL failed: %s",
            context,
            exc,
        )
        return False

    time.sleep(2)
    return True


def _click_get_manual_button(driver, *, context: str, logger: logging.Logger) -> bool:
    """Click the final 'Get manual' button on the download page."""

    try:
        response = driver.execute_script("return window.__manualslibDownloadResponse || null;")
    except Exception:  # pylint: disable=broad-except
        response = None
    if isinstance(response, dict) and response.get("url"):
        logger.debug("(%s) Download response already cached; skipping button click", context)
        return True

    try:
        button = WebDriverWait(driver, 12).until(
            EC.element_to_be_clickable((By.ID, DOWNLOAD_BUTTON_SELECTOR))
        )
    except TimeoutException:
        logger.warning("(%s) 'Get manual' button not found", context)
        return False

    ajax_response = _submit_ajax_get_manual_request(driver, context=context, logger=logger)
    if ajax_response:
        logger.info("(%s) Retrieved download payload via AJAX", context)
        if _navigate_via_cached_response(driver, ajax_response, context=context, logger=logger):
            return True
        logger.debug("(%s) Direct navigation via AJAX payload failed; falling back to DOM click", context)

    logger.debug("(%s) Falling back to DOM click for 'Get manual' button", context)
    return _click_element_with_fallback(
        driver,
        button,
        description="ManualsLib get-manual button",
        logger=logger,
    )


def _click_final_download_link(driver, *, context: str, logger: logging.Logger) -> bool:
    """
    Click the final download link (prefer the direct download URL, fall back to view link).
    """

    response = _get_cached_ajax_download_response(driver)
    if response:
        if _navigate_via_cached_response(driver, response, context=context, logger=logger):
            return True
        logger.debug("(%s) Cached download response present but navigation failed", context)

    selectors = (
        (By.CSS_SELECTOR, DOWNLOAD_LINK_SELECTOR, "download"),
        (By.CSS_SELECTOR, VIEW_LINK_SELECTOR, "view"),
    )
    for by, value, label in selectors:
        try:
            link = WebDriverWait(driver, 12).until(
                EC.element_to_be_clickable((by, value))
            )
        except TimeoutException:
            continue

        driver.execute_script("arguments[0].setAttribute('target','_self');", link)
        href = link.get_attribute("href") or ""
        if href.startswith("//"):
            href = f"https:{href}"
        logger.info("(%s) Clicking final %s link href=%s", context, label, href or "unknown")

        if _click_element_with_fallback(
            driver,
            link,
            description=f"ManualsLib {label} PDF link",
            logger=logger,
        ):
            time.sleep(2)
            return True
        logger.warning("(%s) Failed to click %s link", context, label)

    logger.warning("(%s) Could not locate a download/view link after 'Get manual'", context)
    return False


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
    captcha_present = detect_recaptcha(driver)
    if captcha_present:
        solved = solve_recaptcha_if_present(driver, context=context, logger=logger)
        if not solved:
            logger.warning("(%s) Failed to solve reCAPTCHA challenge", context)
            return False
        logger.info("(%s) Successfully solved reCAPTCHA challenge", context)
    else:
        logger.debug("(%s) No reCAPTCHA iframe detected", context)

    if not click_get_manual:
        return True

    if not _click_get_manual_button(driver, context=context, logger=logger):
        return False

    logger.debug("(%s) Completed CAPTCHA flow and button click", context)
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
                EC.presence_of_element_located((By.ID, PRE_DOWNLOAD_BUTTON_SELECTOR))
            )
        except TimeoutException:
            logger.info("Download button not found within timeout on ManualsLib manual page")
            return None

        download_href = download_button.get_attribute("href") or ""
        if not download_href:
            logger.info("Download button missing href on ManualsLib manual page")
            return None

        download_url = urljoin(manual_url, download_href)
        logger.info("Navigating ManualsLib download page url=%s", download_url)
        safe_driver_get(driver, download_url, timeout=navigation_timeout)

        if not _handle_captcha(driver, click_get_manual=True, context="download page"):
            logger.warning("Aborting ManualsLib scrape due to CAPTCHA failure on download page")
            return None

        if not _click_final_download_link(driver, context="download page", logger=logger):
            logger.warning("Aborting ManualsLib scrape due to missing final download link")
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
