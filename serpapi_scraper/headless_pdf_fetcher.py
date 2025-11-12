import logging
from typing import Optional
from urllib.parse import urlsplit

from app.config import DOWNLOAD_TIMEOUT, USER_AGENT

# Ensure headless utils are available on the path (same approach as orchestrator).
import os
import sys

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

logger = logging.getLogger("serpapi.headless")
DEFAULT_ACCEPT_LANGUAGE = "en-US,en;q=0.9"


def _set_request_headers(driver, referer: Optional[str]) -> None:
    """
    Forward consistent headers (UA + optional referer) through CDP so the PDF
    request mimics a normal browser navigation.
    """
    try:
        driver.execute_cdp_cmd("Network.enable", {})
        headers = {"User-Agent": USER_AGENT, "Accept-Language": DEFAULT_ACCEPT_LANGUAGE}
        if referer:
            headers["Referer"] = referer
        driver.execute_cdp_cmd("Network.setExtraHTTPHeaders", {"headers": headers})
    except Exception as exc:  # pylint: disable=broad-except
        logger.debug("Failed to configure CDP headers for headless download: %s", exc)


def download_pdf_with_headless(
    url: str,
    download_dir: str,
    *,
    referer: Optional[str] = None,
    timeout: int = DOWNLOAD_TIMEOUT,
) -> Optional[str]:
    """
    Fetch a PDF URL using a minimal headless Chrome session.

    This is a generic helper that simply navigates to the URL and waits for
    Chrome's download manager to persist the PDF into `download_dir`. It does
    not attempt any DOM scraping beyond a simple fetch fallback.
    """
    options = get_chrome_options(download_dir)
    driver = create_chrome_driver(options=options, download_dir=download_dir)
    try:
        logger.info(
            "Headless download starting url=%s referer=%s download_dir=%s",
            url,
            referer or "none",
            download_dir,
        )
        _set_request_headers(driver, referer)
        if referer and referer != url:
            try:
                safe_driver_get(driver, referer, timeout=min(timeout, 10))
            except Exception as exc:  # pylint: disable=broad-except
                logger.debug("Pre-navigation to referer failed referer=%s: %s", referer, exc)
        safe_driver_get(driver, url, timeout=timeout)

        pdf_path = wait_for_download(download_dir, timeout=max(timeout, 20))
        if pdf_path:
            logger.info("Headless download succeeded url=%s path=%s", url, pdf_path)
            return pdf_path

        # If direct navigation did not trigger a download, try a fetch-based fallback.
        try:
            driver.execute_async_script(
                """
                const targetUrl = arguments[0];
                const callback = arguments[1];

                fetch(targetUrl, { credentials: 'include' })
                    .then(response => {
                        if (!response.ok) {
                            throw new Error(`HTTP ${response.status}`);
                        }
                        return response.blob();
                    })
                    .then(blob => {
                        const blobUrl = URL.createObjectURL(blob);
                        const anchor = document.createElement('a');
                        anchor.href = blobUrl;
                        anchor.download = '';
                        document.body.appendChild(anchor);
                        anchor.click();
                        setTimeout(() => {
                            URL.revokeObjectURL(blobUrl);
                            anchor.remove();
                            callback(true);
                        }, 250);
                    })
                    .catch(err => {
                        console.error('fetch fallback failed', err);
                        callback(false);
                    });
                """,
                url,
            )
        except Exception as exc:  # pylint: disable=broad-except
            logger.debug("Headless fetch fallback execution failed url=%s: %s", url, exc)

        pdf_path = wait_for_download(download_dir, timeout=15)
        if pdf_path:
            logger.info(
                "Headless fetch fallback succeeded url=%s path=%s", url, pdf_path
            )
            return pdf_path

        logger.warning("Headless download produced no PDF url=%s", url)
        return None
    except Exception as exc:  # pylint: disable=broad-except
        logger.warning("Headless download failed url=%s: %s", url, exc)
        return None
    finally:
        try:
            driver.quit()
        except Exception:  # pylint: disable=broad-except
            logger.debug("Failed to quit headless driver cleanly for url=%s", url)


def get_host(url: str) -> str:
    """Helper to extract normalized host from a URL."""
    try:
        return urlsplit(url).netloc.lower()
    except Exception:  # pylint: disable=broad-except
        return ""
