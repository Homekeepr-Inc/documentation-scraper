"""
Headless scraper for retrieving manuals from ManualsLib.

This module focuses on the happy path needed by the SerpApi orchestrator:
    1. Load the ManualsLib product search result page.
    2. Follow the first manual link in the results list.
    3. Resolve the download button on the manual detail page.
    4. Navigate directly to the download URL so the PDF is saved locally.
"""

from __future__ import annotations

import json
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
# The actual download button ID for ManualsLib.
DOWNLOAD_BUTTON_SELECTOR = "get-manual-button"
DOWNLOAD_LINK_SELECTOR = "a.download-url"
VIEW_LINK_SELECTOR = "a.view-url"
DOWNLOAD_ERROR_SELECTOR = "span.download-error"
CAPTCHA_DOWNLOAD_ERROR_RETRIES = 2


def _preview_data(value: Any, *, limit: int = 600) -> str:
    """Return a truncated, logging-friendly preview of arbitrary data."""

    if value is None:
        return "None"
    if isinstance(value, (dict, list)):
        try:
            text = json.dumps(value, default=str)
        except TypeError:
            text = str(value)
    else:
        text = str(value)
    if len(text) > limit:
        return f"{text[:limit]}...<truncated>"
    return text


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
        if href and "Installation" not in element.text:
            print("element.text %s", element.text)
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
    const captchaInput = block.querySelector('[name="g-recaptcha-response"]') ||
        document.querySelector('[name="g-recaptcha-response"]');
    const idInput = block.querySelector('[name="id"]');
    const payload = {
        captcha: captchaInput ? captchaInput.value : '',
        id: idInput ? idInput.value : '',
        f_hash: window.f_hash || null,
        var1: window.screen ? window.screen.availWidth : null,
        var2: window.screen ? window.screen.availHeight : null,
        var3: document.referrer || ''
    };
    window.__manualslibAjaxPayload = payload;
    const jq = window.jQuery || window.$;
    if (!jq || !jq.post) {
        callback({ok: false, error: 'jquery_missing', payload});
        return;
    }
    jq.post('/download', payload)
        .done(function(resp) {
            window.__manualslibDownloadResponse = resp || {};
            callback({ok: true, resp: resp || {}, payload});
        })
        .fail(function(jqXHR, textStatus, errorThrown) {
            callback({
                ok: false,
                error: (errorThrown || textStatus || 'request_failed'),
                status: jqXHR && jqXHR.status,
                responseText: jqXHR && jqXHR.responseText,
                payload
            });
        });
} catch (err) {
    callback({
        ok: false,
        error: err && err.message ? err.message : String(err),
        payload: window.__manualslibAjaxPayload || null
    });
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
        resp = _normalize_ajax_response(result.get("resp"), context=context, logger=logger)
        payload_snapshot = result.get("payload")
        if resp:
            logger.info(
                "(%s) AJAX payload received keys=%s url=%s customPdfPath=%s raw=%s payload=%s",
                context,
                sorted(resp.keys()),
                resp.get("url"),
                resp.get("customPdfPath"),
                _preview_data(resp),
                _preview_data(payload_snapshot),
            )
            try:
                driver.execute_script("window.__manualslibDownloadResponse = arguments[0] || {};", resp)
            except Exception:  # pylint: disable=broad-except
                pass
            return resp

    logger.warning(
        "(%s) AJAX download request failed: error=%s status=%s raw=%s payload=%s responseText=%s",
        context,
        result.get("error") or "unknown error",
        result.get("status"),
        _preview_data(result.get("resp")),
        _preview_data(result.get("payload")),
        _preview_data(result.get("responseText")),
    )
    return None


def _normalize_ajax_response(
    response: Any,
    *,
    context: str,
    logger: logging.Logger,
) -> Optional[Dict[str, Any]]:
    """
    ManualsLib sometimes returns the AJAX payload as a JSON string; normalize to dict.
    """

    if isinstance(response, dict):
        return response

    if isinstance(response, str):
        text = response.strip()
        if not text:
            return None
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            logger.debug("(%s) Could not parse AJAX response JSON: %s", context, exc)
            return None
        return parsed if isinstance(parsed, dict) else None

    logger.debug("(%s) Unexpected AJAX response type: %s", context, type(response))
    return None


def _install_ajax_capture_hook(
    driver,
    *,
    context: str,
    logger: logging.Logger,
) -> None:
    """
    Override the page's $.post so we can capture the real AJAX response triggered by clicks.
    """

    script = """
if (!window.__manualslibAjaxHookInstalled) {
    window.__manualslibAjaxHookInstalled = true;
    window.__manualslibDownloadPayload = window.__manualslibDownloadPayload || null;
    window.__manualslibAjaxPayload = window.__manualslibAjaxPayload || null;
    window.__manualslibDownloadResponse = window.__manualslibDownloadResponse || null;
    const wrapAjax = function() {
        const jq = window.jQuery || window.$;
        if (!jq || !jq.post || jq.__manualslibPostWrapped) {
            setTimeout(wrapAjax, 400);
            return;
        }
        const originalPost = jq.post;
        jq.post = function(url, data, success, dataType) {
            const request = originalPost.apply(this, arguments);
            if (url === '/download') {
                window.__manualslibDownloadPayload = data || null;
                window.__manualslibAjaxPayload = data || null;
                request.done(function(resp) {
                    window.__manualslibDownloadResponse = resp || {};
                });
                request.fail(function(jqXHR, textStatus, errorThrown) {
                    window.__manualslibDownloadResponse = {
                        error: (errorThrown || textStatus || 'request_failed'),
                        status: jqXHR && jqXHR.status,
                        responseText: jqXHR && jqXHR.responseText
                    };
                });
            }
            return request;
        };
        jq.__manualslibPostWrapped = true;
    };
    wrapAjax();
}
return true;
    """
    try:
        driver.execute_script(script)
        logger.debug("(%s) Installed ManualsLib AJAX capture hook", context)
    except Exception as exc:  # pylint: disable=broad-except
        logger.debug("(%s) Failed to install AJAX capture hook: %s", context, exc)


def _get_cached_ajax_download_response(
    driver,
    *,
    context: str,
    logger: logging.Logger,
    log_missing: bool = True,
) -> Optional[Dict[str, Any]]:
    """Return the cached AJAX response set on the window, if any."""

    try:
        response = driver.execute_script("return window.__manualslibDownloadResponse || null;")
    except Exception:  # pylint: disable=broad-except
        return None
    normalized = _normalize_ajax_response(response, context=context, logger=logger)
    if normalized:
        logger.debug(
            "(%s) Using cached AJAX response keys=%s url=%s customPdfPath=%s",
            context,
            sorted(normalized.keys()),
            normalized.get("url"),
            normalized.get("customPdfPath"),
        )
    else:
        if log_missing:
            logger.debug("(%s) Cached AJAX response missing or invalid", context)
    return normalized


def _get_cached_ajax_payload(driver) -> Optional[Dict[str, Any]]:
    """Return the last AJAX payload stored on the window, if any."""

    try:
        payload = driver.execute_script(
            "return window.__manualslibDownloadPayload || window.__manualslibAjaxPayload || null;"
        )
    except Exception:  # pylint: disable=broad-except
        return None
    if isinstance(payload, dict):
        return payload
    return None


def _wait_for_ajax_download_response(
    driver,
    *,
    context: str,
    logger: logging.Logger,
    timeout: float = 8.0,
) -> Optional[Dict[str, Any]]:
    """Poll for the AJAX response after clicking the button."""

    deadline = time.time() + timeout
    while time.time() < deadline:
        response = _get_cached_ajax_download_response(
            driver,
            context=context,
            logger=logger,
            log_missing=False,
        )
        if response:
            payload = _get_cached_ajax_payload(driver)
            logger.info(
                "(%s) AJAX response detected post-click keys=%s payload=%s",
                context,
                sorted(response.keys()),
                _preview_data(payload),
            )
            return response
        time.sleep(0.35)

    logger.debug("(%s) Timeout waiting for AJAX response after button click", context)
    return None


def _navigate_via_cached_response(
    driver,
    response: Dict[str, Any],
    *,
    context: str,
    logger: logging.Logger,
) -> bool:
    """Navigate directly to the download URL captured from the AJAX response."""

    payload = _get_cached_ajax_payload(driver)
    direct_url = response.get("url") or response.get("customPdfPath")
    logger.debug(
        "(%s) Direct download URL extracted: %s payload=%s",
        context,
        direct_url,
        _preview_data(payload),
    )
    if not isinstance(direct_url, str) or not direct_url:
        logger.warning(
            "(%s) direct_url missing in AJAX payload; payload=%s",
            context,
            _preview_data(response),
        )
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

    # Mark that we've already kicked off the direct download so later steps
    # can skip trying to locate DOM links that will no longer exist.
    setattr(driver, "_manualslib_direct_download", True)
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

    _install_ajax_capture_hook(driver, context=context, logger=logger)

    try:
        button = WebDriverWait(driver, 12).until(
            EC.element_to_be_clickable((By.ID, DOWNLOAD_BUTTON_SELECTOR))
        )
    except TimeoutException:
        logger.warning("(%s) 'Get manual' button not found", context)
        return False

    logger.info("(%s) Clicking 'Get manual' button to trigger real AJAX flow", context)
    if not _click_element_with_fallback(
        driver,
        button,
        description="ManualsLib get-manual button",
        logger=logger,
    ):
        return False

    ajax_response = _wait_for_ajax_download_response(driver, context=context, logger=logger)
    if ajax_response:
        logger.info("(%s) Retrieved download payload via site-triggered AJAX", context)
        if _navigate_via_cached_response(driver, ajax_response, context=context, logger=logger):
            return True
        logger.debug("(%s) Direct navigation via site AJAX payload failed; will retry manual POST", context)

    ajax_response = _submit_ajax_get_manual_request(driver, context=context, logger=logger)
    if ajax_response:
        logger.info("(%s) Retrieved download payload via AJAX", context)
        if _navigate_via_cached_response(driver, ajax_response, context=context, logger=logger):
            return True
        logger.debug("(%s) Direct navigation via AJAX payload failed; falling back to DOM click", context)

    logger.debug("(%s) AJAX attempts exhausted; DOM click already performed", context)
    return True


def _click_final_download_link(driver, *, context: str, logger: logging.Logger) -> bool:
    """
    Click the final download link (prefer the direct download URL, fall back to view link).
    """

    if getattr(driver, "_manualslib_direct_download", False):
        logger.info("(%s) Download already triggered via AJAX payload; skipping final link lookup", context)
        return True

    response = _get_cached_ajax_download_response(driver, context=context, logger=logger)
    if response:
        logger.info(
            "(%s) Attempting direct navigation via cached AJAX response url=%s customPdfPath=%s",
            context,
            response.get("url"),
            response.get("customPdfPath"),
        )
        if _navigate_via_cached_response(driver, response, context=context, logger=logger):
            return True
        logger.debug("(%s) Cached download response present but navigation failed", context)
    else:
        logger.debug("(%s) No cached AJAX response available before final link lookup", context)

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
            logger.debug("(%s) Timeout waiting for %s link using selector %s", context, label, value)
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


def _clear_manualslib_download_state(driver) -> None:
    """Reset any cached AJAX payload/response markers between retries."""

    try:
        driver.execute_script(
            """
            if (window) {
                window.__manualslibDownloadResponse = null;
                window.__manualslibDownloadPayload = null;
                window.__manualslibAjaxPayload = null;
            }
            """
        )
    except Exception:  # pylint: disable=broad-except
        pass

    if hasattr(driver, "_manualslib_direct_download"):
        try:
            delattr(driver, "_manualslib_direct_download")
        except Exception:  # pylint: disable=broad-except
            setattr(driver, "_manualslib_direct_download", False)


def _download_error_present(driver, *, context: str, logger: logging.Logger) -> bool:
    """Check for the ManualsLib download error message or AJAX error payload."""

    response = _get_cached_ajax_download_response(
        driver,
        context=context,
        logger=logger,
        log_missing=False,
    )
    if response:
        has_direct_url = bool(response.get("url") or response.get("customPdfPath"))
        error_text = (response.get("error") or "").strip()
        if error_text and not has_direct_url:
            logger.warning(
                "(%s) Download AJAX response reported error=%s payload=%s",
                context,
                error_text,
                _preview_data(response),
            )
            return True
        if not error_text and not has_direct_url:
            logger.warning(
                "(%s) Download AJAX payload missing direct_url and error text; payload=%s",
                context,
                _preview_data(response),
            )
            return True

    try:
        elements = driver.find_elements(By.CSS_SELECTOR, DOWNLOAD_ERROR_SELECTOR)
    except Exception:  # pylint: disable=broad-except
        elements = []

    for element in elements:
        try:
            text = (element.text or "").strip()
        except Exception:  # pylint: disable=broad-except
            continue
        if not text:
            continue
        if "something went wrong" in text.lower():
            logger.warning("(%s) Download page error message detected: %s", context, text)
            return True

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

    max_attempts = CAPTCHA_DOWNLOAD_ERROR_RETRIES + 1
    for attempt in range(1, max_attempts + 1):
        logger.debug("(%s) Checking for reCAPTCHA challenge attempt=%s", context, attempt)
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

        if not _download_error_present(driver, context=context, logger=logger):
            logger.debug("(%s) Completed CAPTCHA flow and button click", context)
            return True

        if attempt >= max_attempts:
            logger.warning(
                "(%s) Download error persisted after %s attempts; giving up",
                context,
                attempt,
            )
            return False

        logger.info(
            "(%s) Download page error detected post-CAPTCHA; retrying solve (%s/%s)",
            context,
            attempt + 1,
            max_attempts,
        )
        _clear_manualslib_download_state(driver)
        time.sleep(1.0)

    return False


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

    # reCAPTCHA gets upset if we set the user-agent manually, since it knows the real user-agent, somehow.
    # This results in us using the HeadlessChrome UA, but only Cloudflare cares about that one.
    chrome_options = get_chrome_options(download_dir=download_dir)
    chrome_options.arguments = [
        arg for arg in getattr(chrome_options, "arguments", [])
        if not arg.startswith("--user-agent=")
    ]
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
