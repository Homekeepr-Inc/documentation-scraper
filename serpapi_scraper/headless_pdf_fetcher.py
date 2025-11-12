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
BROWSER_ACCEPT_HEADER = "application/pdf,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
BROWSER_SEC_CH_HEADERS = {
    "sec-ch-ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
}


def _set_request_headers(driver, referer: Optional[str]) -> None:
    """
    Forward consistent headers (UA + optional referer) through CDP so the PDF
    request mimics a normal browser navigation.
    """
    try:
        driver.execute_cdp_cmd("Network.enable", {})
        headers = {
            "User-Agent": USER_AGENT,
            "Accept-Language": DEFAULT_ACCEPT_LANGUAGE,
            "Accept": BROWSER_ACCEPT_HEADER,
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-User": "?1",
        }
        headers.update(BROWSER_SEC_CH_HEADERS)
        if referer:
            headers["Referer"] = referer
            headers["Sec-Fetch-Site"] = "same-origin"
        else:
            headers["Sec-Fetch-Site"] = "none"
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
                try:
                    logger.debug(
                        "Headless pre-navigation succeeded referer=%s current_url=%s",
                        referer,
                        driver.current_url,
                    )
                except Exception as exc:  # pylint: disable=broad-except
                    logger.debug("Failed to read current_url after referer nav: %s", exc)
            except Exception as exc:  # pylint: disable=broad-except
                logger.debug("Pre-navigation to referer failed referer=%s: %s", referer, exc)
        safe_driver_get(driver, url, timeout=timeout)
        try:
            logger.debug(
                "Headless navigation completed url=%s current_url=%s title=%s",
                url,
                driver.current_url,
                driver.title,
            )
        except Exception as exc:  # pylint: disable=broad-except
            logger.debug("Failed to read page metadata after navigation url=%s: %s", url, exc)

        pdf_path, download_details = wait_for_download(
            download_dir,
            timeout=max(timeout, 20),
            return_details=True,
            logger=logger.debug,
        )
        if pdf_path:
            logger.info(
                "Headless download succeeded url=%s path=%s metadata=%s",
                url,
                pdf_path,
                download_details,
            )
            return pdf_path
        logger.debug(
            "Headless initial wait produced no download url=%s details=%s",
            url,
            download_details,
        )

        # If direct navigation did not trigger a download, try a fetch-based fallback.
        try:
            if referer and referer != url:
                try:
                    logger.debug("Re-establishing referer context before fetch url=%s referer=%s", url, referer)
                    safe_driver_get(driver, referer, timeout=min(timeout, 10))
                except Exception as exc:  # pylint: disable=broad-except
                    logger.debug("Failed to reload referer before fetch url=%s error=%s", url, exc)

            logger.debug("Attempting headless fetch fallback url=%s", url)
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

        pdf_path, download_details = wait_for_download(
            download_dir,
            timeout=15,
            return_details=True,
            logger=logger.debug,
        )
        if pdf_path:
            logger.info(
                "Headless fetch fallback succeeded url=%s path=%s metadata=%s",
                url,
                pdf_path,
                download_details,
            )
            return pdf_path
        logger.debug(
            "Headless fetch fallback wait produced no download url=%s details=%s",
            url,
            download_details,
        )

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
