#!/usr/bin/env python3
"""
Utility functions for headless scrapers.

This module contains reusable functions that can be used across different
headless browser scrapers, such as fallback mechanisms.
"""

import time
import random
import os
import re
import subprocess
from urllib.parse import urljoin, urlparse
from typing import Iterable, List, Optional

import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import requests
import tempfile
import shutil

# Import config for BLOB_ROOT and PROXY_URL
from app.config import DEFAULT_BLOB_ROOT, PROXY_URL

def _detect_chrome_binary() -> Optional[str]:
    """
    Attempt to locate a Chrome executable that Selenium can launch.

    Preference order:
        1. CHROME_BINARY_PATH environment variable
        2. Standard macOS Google Chrome installation
        3. Google Chrome for Testing bundle
        4. Other Chromium-based installs available on PATH
    """
    env_override = os.getenv("CHROME_BINARY_PATH")
    if env_override:
        candidate = os.path.expanduser(env_override)
        if os.path.exists(candidate):
            return candidate

    candidate_paths = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing",
        "/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary",
        "/usr/bin/google-chrome",
        "/usr/bin/chromium-browser",
        "/usr/bin/chromium",
    ]

    for candidate in candidate_paths:
        if os.path.exists(candidate):
            return candidate

    for candidate in ("google-chrome", "chrome", "chromium-browser", "chromium"):
        resolved = shutil.which(candidate)
        if resolved:
            return resolved

    return None


def _detect_chrome_major_version(binary_path: Optional[str]) -> Optional[int]:
    """Return the major version for the supplied Chrome binary."""

    if not binary_path or not os.path.exists(binary_path):
        return None

    try:
        output = subprocess.check_output([binary_path, "--version"], text=True).strip()
    except Exception:
        return None

    match = re.search(r"(\d+)\.", output)
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def _detect_chromedriver_major_version(driver_path: Optional[str]) -> Optional[int]:
    """Return the major version for an existing chromedriver binary."""

    if not driver_path or not os.path.exists(driver_path):
        return None

    try:
        output = subprocess.check_output([driver_path, "--version"], text=True).strip()
    except Exception:
        return None

    match = re.search(r"ChromeDriver (\d+)\.", output)
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None


def get_chrome_options(download_dir=None):
    """
    Build ChromeOptions with common scraper defaults and optional download directory.

    Args:
        download_dir (str, optional): Directory where Chrome should store downloads.

    Returns:
        ChromeOptions: Configured options instance.
    """
    options = ChromeOptions()
    if os.getenv('HEADLESS', 'true').lower() != 'false':
        options.add_argument('--headless')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1280,720')
    options.add_argument('--disable-popup-blocking')
    options.add_argument('--disable-images')
    options.add_argument('--disable-plugins')
    options.add_argument('--disable-extensions')
    # NEVER use the HeadlessChrome user-agent. Cloudflare will force a captcha on us.
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.3')

    if PROXY_URL:
        options.add_argument(f'--proxy-server={PROXY_URL}')
        print(f"Using proxy server {PROXY_URL}")
    else:
        print("**NO PROXY CONFIGURED** - running without proxy")

    if download_dir:
        options.add_experimental_option("prefs", {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True,
        })

    return options


def create_chrome_driver(options=None, download_dir=None):
    """
    Create a Chrome driver. Uses auto-download for local testing if USE_TESTING_CHROMEDRIVER=true, otherwise uses system chromedriver for production/Docker.

    Args:
        options (ChromeOptions, optional): Chrome options. If None, uses get_chrome_options().
        download_dir (str, optional): Download directory for options.

    Returns:
        Chrome driver instance
    """
    if options is None:
        options = get_chrome_options(download_dir)

    chrome_binary = _detect_chrome_binary()
    if chrome_binary:
        try:
            options.binary_location = chrome_binary
            print(f"Using Chrome binary at {chrome_binary}")
        except Exception:
            print(f"Detected Chrome binary at {chrome_binary} but failed to assign to options.")

    detected_major = _detect_chrome_major_version(chrome_binary)
    if detected_major:
        print(f"Detected Chrome major version {detected_major}")

    use_testing_driver = os.getenv('USE_TESTING_CHROMEDRIVER', '').lower() == 'true'
    system_driver_path = '/usr/bin/chromedriver'

    driver_executable_path = None
    if not use_testing_driver and os.path.exists(system_driver_path):
        print(f"Using system chromedriver at {system_driver_path}")
        driver_executable_path = system_driver_path
    else:
        temp_dir = tempfile.mkdtemp(prefix="chromedriver_", suffix="_temp")
        patcher = uc.Patcher(
            version_main=detected_major or 0,
            force=True,
        )
        patcher.data_path = temp_dir
        patcher.zip_path = os.path.join(temp_dir, "undetected")
        exe_basename = os.path.basename(patcher.executable_path)
        patcher.executable_path = os.path.join(temp_dir, exe_basename)
        patcher.auto()
        driver_executable_path = patcher.executable_path
        downloaded_major = _detect_chromedriver_major_version(driver_executable_path)
        if detected_major and downloaded_major and downloaded_major != detected_major:
            print(
                f"Warning: downloaded chromedriver major version {downloaded_major} does not match "
                f"Chrome major version {detected_major}."
            )
        print(f"Temp chromedriver ready at {driver_executable_path}")

    # Explicitly pass parameters to avoid unpacking issues
    driver = uc.Chrome(
        options=options,
        browser_executable_path=chrome_binary,
        version_main=detected_major,
        driver_executable_path=driver_executable_path
    )

    target_download_dir = download_dir
    if not target_download_dir and options is not None:
        try:
            download_prefs = {}
            prefs_container = getattr(options, "experimental_options", None)
            if not prefs_container and hasattr(options, "_experimental_options"):
                prefs_container = getattr(options, "_experimental_options")
            if isinstance(prefs_container, dict):
                download_prefs = prefs_container.get("prefs", {}) or {}
            if download_prefs:
                target_download_dir = download_prefs.get("download.default_directory")
        except Exception:
            target_download_dir = None

    if target_download_dir:
        try:
            driver.execute_cdp_cmd(
                "Page.setDownloadBehavior",
                {
                    "behavior": "allow",
                    "downloadPath": target_download_dir,
                    "eventsEnabled": True,
                },
            )
        except Exception as err:
            print(f"Failed to enable Chrome downloads to {target_download_dir}: {err}")

    return driver


def safe_driver_get(driver, url, timeout=15):
    """
    Safely navigate to a URL with a page load timeout.

    Sets the page load timeout to the specified value, attempts to load the page,
    and if it times out, logs a warning but continues execution. This prevents
    indefinite waiting on pages that never fully load.

    Args:
        driver: Selenium WebDriver instance
        url (str): The URL to navigate to
        timeout (int): Timeout in seconds for page load (default 10)
    """
    driver.set_page_load_timeout(timeout)
    try:
        driver.get(url)
    except TimeoutException:
        print(f"Page load timed out after {timeout} seconds for {url}, continuing anyway.")


def _normalize_host(host: str) -> str:
    """Normalize a host/domain string for comparison purposes."""

    if not host:
        return ""

    candidate = host.strip().lower()
    if not candidate:
        return ""

    if "://" not in candidate:
        candidate = f"https://{candidate}"

    parsed = urlparse(candidate)
    return parsed.netloc or parsed.path or ""


def generate_model_candidates(model: str, max_trim: int = 0) -> List[str]:
    """
    Build a list of model-number variants to broaden searches/matching.

    Normalizes whitespace/separators and optionally trims trailing characters, which helps
    when manufacturers publish manuals under slightly shortened model numbers.
    """
    if not model:
        return []

    raw = model.strip()
    if not raw:
        return []

    separator_pattern = re.compile(r"[\s\-_/\.]+")
    variants: List[str] = []
    seen = set()

    def add(candidate: str):
        candidate = candidate.strip()
        if not candidate or candidate in seen:
            return
        variants.append(candidate)
        seen.add(candidate)

    add(raw)

    normalized_space = separator_pattern.sub(" ", raw)
    add(normalized_space)

    collapsed = separator_pattern.sub("", raw)
    add(collapsed)

    hyphenated = separator_pattern.sub("-", raw).strip("-")
    add(hyphenated)

    def add_trimmed(value: str):
        trimmed = value
        for _ in range(max_trim):
            trimmed = trimmed[:-1].rstrip("-_/ .")
            if len(trimmed) < 3:
                break
            add(trimmed)

    add_trimmed(raw)
    add_trimmed(collapsed)

    return variants


def match_model_in_text(text: str, model: str, max_trim: int = 0) -> Optional[str]:
    """
    Attempt to find any model-number variant within the provided text.

    Returns the first variant that matches (case-insensitive), allowing for trimmed or
    separator-free forms to catch loosely formatted product pages.
    """
    if not text or not model:
        return None

    lowered_text = text.lower()
    compact_text = re.sub(r"[\s\-_/\.]+", "", lowered_text)

    for candidate in generate_model_candidates(model, max_trim=max_trim):
        candidate_lower = candidate.lower()
        if candidate_lower and candidate_lower in lowered_text:
            return candidate

        compact_candidate = re.sub(r"[\s\-_/\.]+", "", candidate_lower)
        if compact_candidate and compact_candidate in compact_text:
            return candidate

    return None


def duckduckgo_fallback(
    driver,
    model,
    host_url,
    scrape_callback,
    search_query=None,
    max_model_trim: int = 0,
    allowed_hosts: Optional[Iterable[str]] = None,
    disallowed_url_substrings: Optional[Iterable[str]] = None,
):
    """
    Generic DuckDuckGo fallback mechanism for finding manuals when direct scraping fails.

    Attempts the provided search query (or a default one) and progressively trims the trailing
    characters from the model number when `max_model_trim` is greater than zero. Restrict results
    with `allowed_hosts`, exclude known-bad URLs via `disallowed_url_substrings`, and skip direct
    PDF links to avoid bypassing product detail pages the callbacks depend on.
    """

    print(f"Attempting DuckDuckGo fallback for {model} on {host_url}...")

    variants = generate_model_candidates(model, max_trim=max_model_trim)
    if not variants:
        variants = [model]

    # Ensure the exact model is first in the list
    if model not in variants:
        variants.insert(0, model)

    base_query = search_query
    tried_queries = set()

    host_url_lower = host_url.lower() if host_url else ""

    normalized_allowed_hosts = None
    normalized_disallowed = None
    if allowed_hosts:
        normalized_allowed_hosts = set()
        for host in allowed_hosts:
            normalized = _normalize_host(host)
            if normalized:
                normalized_allowed_hosts.add(normalized)
        if not normalized_allowed_hosts:
            normalized_allowed_hosts = None
    if disallowed_url_substrings:
        normalized_disallowed = [
            substring.lower()
            for substring in disallowed_url_substrings
            if substring
        ]
        if not normalized_disallowed:
            normalized_disallowed = None

    for variant in variants:
        if base_query is None:
            query = f"\"{variant}\" site:{host_url}"
        else:
            if '{model}' in base_query:
                query = base_query.format(model=variant)
            elif model and model in base_query:
                query = base_query.replace(model, variant)
            else:
                query = base_query

        if query in tried_queries:
            continue
        tried_queries.add(query)

        try:
            print(f"Running DuckDuckGo search for query: {query}")
            safe_driver_get(driver, f"https://duckduckgo.com/?q={query}")
            print(f"DuckDuckGo search loaded for query: {query}")

            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a[data-testid='result-title-a']"))
            )

            result_links = driver.find_elements(By.CSS_SELECTOR, "a[data-testid='result-title-a'], .result__a, .result__url")

            trusted_link = None
            for link in result_links:
                href = link.get_attribute('href')
                if href and 'duckduckgo.com' in href.lower():
                    continue
                if not href:
                    continue

                href_lower = href.lower()
                parsed = urlparse(href_lower)
                path_lower = parsed.path or ""
                if path_lower.endswith(".pdf") or ".pdf" in href_lower:
                    print(f"Ignoring candidate link for query '{query}' because it points directly to a PDF: {href}")
                    continue

                if normalized_disallowed and any(substring in href_lower for substring in normalized_disallowed):
                    print(
                        f"Ignoring candidate link for query '{query}' due to disallowed substring match: {href}"
                    )
                    continue

                if normalized_allowed_hosts:
                    link_host = (parsed.netloc or "").lower()
                    if link_host in normalized_allowed_hosts:
                        print(f"Found trusted link for query '{query}': {href}")
                        trusted_link = link
                        break
                    else:
                        print(f"Ignoring candidate link for query '{query}' due to unmatched host '{link_host}': {href}")
                        continue
                elif host_url_lower and host_url_lower in href_lower:
                    print(f"Found trusted link for query '{query}': {href}")
                    trusted_link = link
                    break

            if not trusted_link:
                print(f"No trusted link found for {host_url} using query '{query}'")
                continue

            try:
                trusted_link.click()
                time.sleep(0.2)
                print(f"Navigated to: {driver.current_url}")
                return scrape_callback(driver)
            except Exception as e:
                print(f"Navigation failed: {e}, attempting callback anyway on current page")
                try:
                    return scrape_callback(driver)
                except Exception as e2:
                    print(f"Callback failed anyway: {e2}")
                    return None

        except Exception as e:
            print(f"DuckDuckGo search attempt failed for query '{query}': {e}")
            continue

    print(f"DuckDuckGo fallback failed for {model} after trying {len(tried_queries)} queries.")
    return None


def _case_insensitive_xpath(tag: str, text: str) -> str:
    """Construct a case-insensitive XPath expression for the supplied tag/text."""

    lowered = text.lower()
    return (
        f"//{tag}[contains(translate(normalize-space(string(.)), "
        "'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), "
        f"'{lowered}')]"
    )


def _find_link_with_text(driver, text: str):
    """Find an anchor element matching the text value, ignoring case where necessary."""

    strategies = [
        (By.LINK_TEXT, text),
        (By.PARTIAL_LINK_TEXT, text),
    ]
    for by, value in strategies:
        try:
            return driver.find_element(by, value)
        except Exception:
            continue

    try:
        elements = driver.find_elements(By.XPATH, _case_insensitive_xpath('a', text))
        if elements:
            return elements[0]
    except Exception:
        pass
    return None


def homedepot_manual_callback(
    driver,
    model: str,
    *,
    manual_link_texts: Optional[Iterable[str]] = None,
    expand_headers: Optional[Iterable[str]] = None,
    scroll_offsets: Optional[Iterable[int]] = None,
    max_model_trim: int = 3,
    wait_for_header: int = 5,
    wait_for_manual_link: int = 10,
):
    """Generic HomeDepot.com manual scraping callback for DuckDuckGo fallback flows."""

    try:
        print(f"Starting Home Depot callback for model {model}")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
        )
        print("Home Depot page body loaded.")

        page_source = driver.page_source or ""
        matched_model = match_model_in_text(page_source, model, max_trim=max_model_trim)
        if matched_model:
            print(f"Matched model variant on page: {matched_model}")
        else:
            print("No direct model match found in page source; continuing with manual search.")

        offsets = list(scroll_offsets) if scroll_offsets is not None else [400, 800, 1200]
        for offset in offsets:
            try:
                driver.execute_script("window.scrollTo(0, arguments[0]);", offset)
                time.sleep(0.2)
            except Exception as scroll_err:
                print(f"Scrolling to offset {offset} failed: {scroll_err}")

        headers = list(expand_headers) if expand_headers is not None else ["Product Details"]
        for header in headers:
            try:
                header_locator = (
                    By.XPATH,
                    _case_insensitive_xpath('h3', header)
                )
                element = WebDriverWait(driver, wait_for_header).until(
                    EC.element_to_be_clickable(header_locator)
                )
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                time.sleep(0.2)
                driver.execute_script("arguments[0].click();", element)
                print(f"Expanded section '{header}'.")
                time.sleep(0.2)
            except Exception as header_err:
                print(f"Failed to expand section '{header}': {header_err}")

        texts = list(manual_link_texts) if manual_link_texts is not None else [
            "Use and Care Manual",
            "Use & Care Manual",
            "Owner's Manual",
        ]

        manual_link = None
        for text in texts:
            manual_link = _find_link_with_text(driver, text)
            if manual_link:
                print(f"Found manual link using text '{text}'.")
                break

        if not manual_link:
            print("Failed to locate manual link on Home Depot page.")
            return None

        WebDriverWait(driver, wait_for_manual_link).until(
            EC.element_to_be_clickable(manual_link)
        )

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", manual_link)
        time.sleep(0.2)
        driver.execute_script("arguments[0].click();", manual_link)

        file_url = manual_link.get_attribute("href")
        if file_url:
            file_url = urljoin(driver.current_url, file_url)

        if file_url:
            print(f"Navigating to manual URL: {file_url}")
            safe_driver_get(driver, file_url)
            time.sleep(0.2)
        else:
            print("Manual link missing href; relying on navigation after click.")

        if len(driver.window_handles) > 1:
            print("New window detected for manual, switching...")
            current_handle = driver.current_window_handle
            for handle in driver.window_handles:
                if handle != current_handle:
                    driver.switch_to.window(handle)
                    time.sleep(0.2)
                    break

        source_url = driver.current_url if driver.current_url != 'about:blank' else file_url
        final_title = manual_link.text.strip() if manual_link.text else "Home Depot Manual"

        return {
            'file_url': file_url or source_url,
            'title': final_title,
            'source_url': source_url,
            'matched_model': matched_model,
        }

    except Exception as err:
        print(f"Error in Home Depot callback: {err}")
        return None


def validate_pdf_file(file_path):
    """
    Validate that a file is a valid PDF.

    Args:
        file_path (str): Path to the file to validate

    Returns:
        bool: True if file is a valid PDF, False otherwise
    """
    try:
        with open(file_path, 'rb') as f:
            content = f.read(10)
        return content.startswith(b'%PDF-')
    except Exception as e:
        print(f"Error validating PDF {file_path}: {e}")
        return False


def validate_pdf_content(file_path, model):
    """
    Validate that the PDF content contains the model number.

    Args:
        file_path (str): Path to the PDF file
        model (str): Model number to check for

    Returns:
        bool: True if model is found in PDF text, False otherwise
    """
    try:
        from pypdf import PdfReader
        import io

        with open(file_path, 'rb') as f:
            pdf_bytes = f.read()

        reader = PdfReader(io.BytesIO(pdf_bytes))
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
            if len(text) > 10000:  # Limit to first 10k chars
                break

        # Check if model is in text (case insensitive)
        return model.lower() in text.lower()
    except Exception as e:
        print(f"Error validating PDF content {file_path}: {e}")
        return False


def wait_for_download(
    download_dir,
    timeout=30,
    *,
    initial_files=None,
    expected_filename=None,
    expected_extensions=(".pdf",),
    poll_interval=0.2,
    return_details=False,
    logger=None,
):
    """
    Wait for a download to complete in the specified directory.

    Args:
        download_dir (str): Directory to monitor for downloads.
        timeout (int): Maximum time to wait in seconds.
        initial_files (Iterable[str], optional): Snapshot of filenames present before the download started.
        expected_filename (str, optional): Desired filename (or prefix) to filter matches.
        expected_extensions (Tuple[str], optional): Allowed file extensions. Defaults to ('.pdf',).
        poll_interval (float, optional): Seconds to sleep between directory polls.
        return_details (bool, optional): When True, return (path, info_dict); otherwise just the path.
        logger (Callable[[str], None], optional): Optional callable for debug logging.

    Returns:
        str or (str, dict): Path to the downloaded file, or None if timeout/no match.
                            When return_details=True, a tuple of (path, details_dict) is returned.
    """
    start_time = time.time()
    known_files = set(initial_files) if initial_files is not None else set(os.listdir(download_dir))
    seen_pending = set()
    expected_filename_normalized = None
    expected_prefix = None
    if expected_filename:
        expected_filename_normalized = expected_filename.strip().lower()
        expected_prefix, expected_ext = os.path.splitext(expected_filename_normalized)
    if isinstance(expected_extensions, str):
        expected_extensions = (expected_extensions,)
    expected_extensions = tuple(ext.lower() for ext in expected_extensions)

    last_pending = []
    other_new_files = []

    def _log(message):
        if logger:
            logger(message)

    while time.time() - start_time < timeout:
        try:
            current_entries = os.listdir(download_dir)
        except FileNotFoundError:
            time.sleep(poll_interval)
            continue

        current_set = set(current_entries)
        new_entries = current_set - known_files
        if new_entries:
            known_files.update(new_entries)

        candidate_paths = []
        candidate_names = []
        pending = []

        for entry in current_entries:
            entry_path = os.path.join(download_dir, entry)
            if not os.path.isfile(entry_path):
                continue

            entry_lower = entry.lower()

            if entry_lower.endswith(".crdownload"):
                pending.append(entry)
                if entry not in seen_pending:
                    _log(f"Download in progress: {entry}")
                    seen_pending.add(entry)
                continue

            if expected_extensions and not any(entry_lower.endswith(ext) for ext in expected_extensions):
                continue

            if expected_filename_normalized:
                candidate_lower = entry_lower
                if candidate_lower != expected_filename_normalized:
                    candidate_base, _candidate_ext = os.path.splitext(candidate_lower)
                    if not candidate_base.startswith(expected_prefix or ""):
                        continue

            # Ignore files that existed before and have not been modified recently.
            if entry in known_files and entry not in new_entries:
                try:
                    if os.path.getmtime(entry_path) <= start_time:
                        continue
                except OSError:
                    continue

            candidate_paths.append(entry_path)
            candidate_names.append(entry)

        if new_entries:
            other_new = [
                entry
                for entry in new_entries
                if entry not in candidate_names and entry not in pending
            ]
            if other_new:
                other_new_files.extend(other_new)

        last_pending = pending

        if candidate_paths:
            candidate_paths.sort(key=lambda path: os.path.getmtime(path), reverse=True)
            result_path = candidate_paths[0]
            details = {
                "new_files": candidate_names,
                "pending": pending,
                "other_new_files": other_new_files,
                "elapsed": time.time() - start_time,
                "timed_out": False,
            }
            return (result_path, details) if return_details else result_path

        time.sleep(poll_interval)

    details = {
        "new_files": [],
        "pending": last_pending,
        "other_new_files": other_new_files,
        "elapsed": time.time() - start_time,
        "timed_out": True,
    }
    return (None, details) if return_details else None


def trigger_fetch_download(driver, file_url: str, filename: str):
    """
    Initiate a blob-based download via the browser when a direct click does not yield a local file.
    Returns True if the browser signalled that the fetch completed successfully.
    """
    try:
        return driver.execute_async_script(
            """
            const url = arguments[0];
            const filename = arguments[1];
            const callback = arguments[2];

            fetch(url, { credentials: 'include' })
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
                    anchor.download = filename;
                    document.body.appendChild(anchor);
                    anchor.click();
                    setTimeout(() => {
                        URL.revokeObjectURL(blobUrl);
                        anchor.remove();
                        callback(true);
                    }, 500);
                })
                .catch(err => {
                    console.error('Fetch-based download fallback failed:', err);
                    callback(false);
                });
            """,
            file_url,
            filename,
        )
    except Exception as err:
        print(f"Fetch-based fallback execution failed: {err}")
        return False


def ensure_pdf_download(
    driver,
    element,
    download_dir: str,
    *,
    file_url: Optional[str] = None,
    preferred_filename: Optional[str] = None,
    timeout: int = 30,
    fetch_timeout: int = 30,
    fetch_on_failure: bool = True,
    scroll_into_view: bool = True,
    poll_interval: float = 0.2,
):
    """
    Attempt to download a PDF by clicking the supplied element and monitoring the download directory.

    Returns a tuple of (pdf_path, info_dict) where pdf_path may be None when no completed PDF is detected.
    The info dict contains diagnostic metadata useful for debugging failures.
    """
    initial_files = set(os.listdir(download_dir))

    filename = (preferred_filename or "").strip()
    if not filename and file_url:
        filename = os.path.basename(urlparse(file_url).path or "")
    if filename:
        if not filename.lower().endswith(".pdf"):
            filename = f"{filename}.pdf"
    else:
        filename = f"manual-{int(time.time())}.pdf"

    diagnostics = {
        "filename": filename,
        "fetch_triggered": False,
        "errors": [],
    }

    # Prepare the element for a same-tab download.
    try:
        driver.execute_script("arguments[0].setAttribute('target', '_self');", element)
    except Exception as err:
        diagnostics["errors"].append(f"set_target:{err}")
    try:
        driver.execute_script("arguments[0].setAttribute('download', arguments[1]);", element, filename)
    except Exception as err:
        diagnostics["errors"].append(f"set_download:{err}")

    if scroll_into_view:
        try:
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.2)
        except Exception as err:
            diagnostics["errors"].append(f"scroll:{err}")

    try:
        driver.execute_script("arguments[0].click();", element)
    except Exception as err:
        diagnostics["errors"].append(f"click:{err}")

    pdf_path, details = wait_for_download(
        download_dir,
        timeout=timeout,
        initial_files=initial_files,
        expected_filename=filename,
        poll_interval=poll_interval,
        return_details=True,
    )

    diagnostics.update(details)

    if pdf_path:
        return pdf_path, diagnostics

    if not pdf_path and fetch_on_failure and file_url:
        diagnostics["fetch_triggered"] = bool(
            trigger_fetch_download(driver, file_url, filename)
        )
        pdf_path, details = wait_for_download(
            download_dir,
            timeout=fetch_timeout,
            initial_files=initial_files,
            expected_filename=filename,
            poll_interval=poll_interval,
            return_details=True,
        )
        diagnostics.update(details)

    return pdf_path, diagnostics

# validate_content is broken as most manufacturers do not inject the real model name into the pdf.
# They usually just mention the model series name vs specific model numbers.
# Because of that, validate_content is set to False by default.
def validate_and_ingest_manual(result, validate_content=False):
    """
    Validate and ingest a scraped manual result into the database.

    Performs PDF validation and optionally content validation against the model number.

    Args:
        result (dict): Scraped result containing brand, model_number, doc_type, title, source_url, file_url
                       Optionally local_path if downloaded locally.
        validate_content (bool): Whether to validate that PDF content contains the model number

    Returns:
        IngestResult: Result of the ingestion, or None if validation fails
    """
    if not result:
        return None

    local_path = result.get('local_path')
    model = result['model_number']

    if local_path:
        # Validate PDF file
        if not validate_pdf_file(local_path):
            print(f"Invalid PDF file: {local_path}")
            return None

        # Validate content if requested
        if validate_content and not validate_pdf_content(local_path, model):
            print(f"PDF content does not contain model {model}: {local_path}")
            return None

    # Import here to avoid circular imports
    from app.ingest import ingest_from_local_path, ingest_from_url
    if local_path:
        return ingest_from_local_path(
            brand=result['brand'],
            model_number=result['model_number'],
            doc_type=result['doc_type'],
            title=result['title'],
            source_url=result['source_url'],
            file_url=result['file_url'],
            local_path=result['local_path']
        )
    else:
        return ingest_from_url(
            brand=result['brand'],
            model_number=result['model_number'],
            doc_type=result['doc_type'],
            title=result['title'],
            source_url=result['source_url'],
            file_url=result['file_url']
        )


def ingest_manual(result):
    """
    Generic function to ingest a scraped manual result into the database.
    DEPRECATED: Use validate_and_ingest_manual instead for better validation.

    Args:
        result (dict): Scraped result containing brand, model_number, doc_type, title, source_url, file_url
                        Optionally local_path if downloaded locally.

    Returns:
        IngestResult: Result of the ingestion
    """
    print("WARNING: ingest_manual is deprecated. Use validate_and_ingest_manual instead.")
    return validate_and_ingest_manual(result, validate_content=False)


def create_temp_download_dir():
    """
    Create a unique temporary directory for PDF downloads.

    Returns:
        str: Path to the temporary directory
    """
    # Create temp dir relative to the scraper directory
    scraper_dir = os.path.dirname(__file__)
    temp_base = os.path.join(scraper_dir, 'temp')
    os.makedirs(temp_base, exist_ok=True)
    return tempfile.mkdtemp(dir=temp_base)


def cleanup_temp_dir(temp_dir):
    """
    Safely remove a temporary directory and its contents.

    Args:
        temp_dir (str): Path to the temporary directory to remove
    """
    try:
        shutil.rmtree(temp_dir)
    except Exception as e:
        print(f"Error cleaning up temp dir {temp_dir}: {e}")
