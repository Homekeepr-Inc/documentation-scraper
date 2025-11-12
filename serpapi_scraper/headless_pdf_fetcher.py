"""
Minimal headless PDF fetcher used by the SerpApi orchestrator.

The older implementation attempted to emulate full site-specific scrapers which
made maintenance difficult.  This helper focuses purely on establishing cookies
via a warm-up navigation and then downloading the requested PDF while mimicking
normal browser behaviour.
"""

from __future__ import annotations

import contextlib
import logging
import os
import random
import sys
import time
from typing import Optional
from urllib.parse import urlparse, urlunparse

from app.config import DOWNLOAD_TIMEOUT

# Reuse the shared headless utilities so we inherit consistent browser settings.
HEADLESS_UTILS_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "headless-browser-scraper")
)
if HEADLESS_UTILS_PATH not in sys.path:
    sys.path.append(HEADLESS_UTILS_PATH)

from utils import (  # type: ignore  # pylint: disable=import-error
    create_chrome_driver,
    get_chrome_options,
    safe_driver_get,
    trigger_fetch_download,
    wait_for_download,
)

logger = logging.getLogger("serpapi.headless_pdf_fetcher")

# Allow a little extra time compared to synchronous requests so the download can complete.
DEFAULT_NAVIGATION_TIMEOUT = max(20, DOWNLOAD_TIMEOUT)
DEFAULT_DOWNLOAD_TIMEOUT = max(30, DOWNLOAD_TIMEOUT + 10)


def get_host(url: str) -> str:
    """
    Return the normalized host for a URL.

    Falls back to an empty string when parsing fails so callers can short-circuit.
    """
    if not url:
        return ""
    try:
        parsed = urlparse(url)
    except Exception:  # pylint: disable=broad-except
        return ""

    host = parsed.netloc or ""
    return host.lower()


def _build_root_url(url: str) -> Optional[str]:
    """Best-effort attempt to derive a root URL for warm-up navigation."""
    if not url:
        return None
    try:
        parsed = urlparse(url)
    except Exception:  # pylint: disable=broad-except
        return None

    host = parsed.netloc
    if not host:
        return None

    scheme = parsed.scheme or "https"
    root_parts = (scheme, host, "/", "", "", "")
    return urlunparse(root_parts)


def _sleep_jitter(base: float, spread: float = 0.75) -> None:
    """Pause briefly with jitter to mimic natural browsing cadence."""
    delay = base + random.uniform(0, spread)  # nosec B311
    time.sleep(delay)


def download_pdf_with_headless(
    url: str,
    download_dir: str,
    *,
    referer: Optional[str] = None,
    navigation_timeout: int = DEFAULT_NAVIGATION_TIMEOUT,
    download_timeout: int = DEFAULT_DOWNLOAD_TIMEOUT,
) -> Optional[str]:
    """
    Use a headless Chrome session to download a PDF.

    The driver first navigates to a warm-up page (either the provided referer or the
    derived root domain) so that any required cookies/session data are established.
    It then loads the direct PDF URL and waits for Chrome's download manager to
    finish writing the file.  As a fallback we execute an in-browser fetch to trigger
    a manual download in case the navigation was intercepted by the site.
    """
    if not url or not download_dir:
        logger.debug("Headless fetch skipped because url or download_dir missing")
        return None

    os.makedirs(download_dir, exist_ok=True)

    host = get_host(url)
    initial_snapshot = set(os.listdir(download_dir))

    chrome_options = get_chrome_options(download_dir=download_dir)
    driver = create_chrome_driver(options=chrome_options, download_dir=download_dir)

    try:
        warmup_url = referer or _build_root_url(url)
        if warmup_url:
            try:
                logger.debug("Headless warm-up navigation url=%s", warmup_url)
                safe_driver_get(driver, warmup_url, timeout=navigation_timeout)
                _sleep_jitter(0.6)
            except Exception as exc:  # pylint: disable=broad-except
                logger.info("Warm-up navigation failed url=%s error=%s", warmup_url, exc)

        logger.info("Headless PDF navigation url=%s host=%s", url, host or "unknown")
        try:
            safe_driver_get(driver, url, timeout=navigation_timeout)
        except Exception as exc:  # pylint: disable=broad-except
            logger.info("Primary PDF navigation raised error url=%s error=%s", url, exc)

        pdf_path = wait_for_download(
            download_dir,
            timeout=download_timeout,
            initial_files=initial_snapshot,
            expected_extensions=(".pdf",),
        )
        if pdf_path:
            logger.info("Headless download succeeded url=%s path=%s", url, pdf_path)
            return pdf_path

        # Fallback: return to the warm-up page (if available) and trigger a fetch-based download.
        fallback_context_url = warmup_url or _build_root_url(url)
        if fallback_context_url:
            try:
                safe_driver_get(driver, fallback_context_url, timeout=navigation_timeout)
                _sleep_jitter(0.4)
            except Exception as exc:  # pylint: disable=broad-except
                logger.debug(
                    "Failed to re-establish context before fetch fallback url=%s error=%s",
                    fallback_context_url,
                    exc,
                )

        filename = os.path.basename(urlparse(url).path or "") or f"manual-{int(time.time())}.pdf"
        if not filename.lower().endswith(".pdf"):
            filename = f"{filename}.pdf"

        logger.debug("Attempting fetch-based download fallback filename=%s", filename)
        try:
            fetch_triggered = trigger_fetch_download(driver, url, filename)
        except Exception as exc:  # pylint: disable=broad-except
            logger.info("Fetch-based fallback raised error url=%s error=%s", url, exc)
            fetch_triggered = False

        if fetch_triggered:
            pdf_path = wait_for_download(
                download_dir,
                timeout=download_timeout,
                initial_files=initial_snapshot,
                expected_filename=filename,
                expected_extensions=(".pdf",),
            )
            if pdf_path:
                logger.info("Fetch-based download succeeded url=%s path=%s", url, pdf_path)
                return pdf_path

        logger.warning("Headless PDF fetch failed url=%s host=%s", url, host or "unknown")
        return None
    finally:
        with contextlib.suppress(Exception):
            driver.quit()
