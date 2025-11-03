#!/usr/bin/env python3
"""
Whirlpool Appliance Manuals Headless Scraper

Uses undetected-chromedriver for stealthy headless scraping to avoid bot detection.
Extracts owner's manual PDFs from whirlpool.com.

Usage: python3 whirlpool_headless_scraper.py <model_number1> <model_number2> ...

Example: python3 whirlpool_headless_scraper.py WRT311FZDW
"""

import sys
import os
import time
import random
from urllib.parse import urljoin, urlparse

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
# Import utility functions
sys.path.append(os.path.dirname(__file__))
from utils import (
    safe_driver_get,
    validate_and_ingest_manual,
    create_temp_download_dir,
    cleanup_temp_dir,
    get_chrome_options,
    create_chrome_driver,
    wait_for_download,
    duckduckgo_fallback,
)

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.config import DEFAULT_BLOB_ROOT


def whirlpool_duckduckgo_callback(driver, model: str, download_dir: str):
    """Find, download, and return the Whirlpool owner's manual PDF via DuckDuckGo fallback."""

    try:
        print(f"Starting Whirlpool DuckDuckGo callback for model {model}")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        product_url = driver.current_url
        print(f"Whirlpool product page loaded: {product_url}")

        link_locator = (
            By.CSS_SELECTOR,
            'a.documents-component__content-section-link[aria-label="Download Owner\'s Manual"]',
        )
        manual_link = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(link_locator)
        )
        print("Located Owner's Manual link on Whirlpool page.")

        aria_label = (manual_link.get_attribute("aria-label") or "").strip()
        if aria_label.lower() != "download owner's manual":
            print(f"Owner's Manual link aria-label mismatch: '{aria_label}'")
            return None

        raw_href = manual_link.get_attribute("href")
        if not raw_href:
            print("Owner's Manual link missing href attribute.")
            return None

        file_url = urljoin(product_url, raw_href)
        print(f"Resolved Owner's Manual URL: {file_url}")

        files_before = set(os.listdir(download_dir))
        filename = os.path.basename(urlparse(file_url).path) or f"{model}.pdf"
        if not filename.lower().endswith('.pdf'):
            filename = f"{filename}.pdf"

        # Force the link to download within the current tab instead of opening a viewer.
        driver.execute_script(
            "arguments[0].setAttribute('target', '_self'); arguments[0].setAttribute('download', arguments[1]);",
            manual_link,
            filename,
        )
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", manual_link)
        time.sleep(0.2)
        driver.execute_script("arguments[0].click();", manual_link)
        print("Clicked Owner's Manual link.")

        pdf_path = wait_for_download(download_dir, timeout=30)
        if pdf_path:
            print(f"Downloaded PDF during Whirlpool fallback: {pdf_path}")
        else:
            files_after = set(os.listdir(download_dir))
            new_files = files_after - files_before
            if new_files:
                newest = max(
                    (os.path.join(download_dir, fname) for fname in new_files),
                    key=os.path.getmtime,
                )
                print(f"Detected new file after click without wait_for_download match: {newest}")
                pdf_path = newest if newest.lower().endswith('.pdf') else None

        # As a fallback, trigger an in-page fetch + download to force Chrome to stream the PDF.
        if not pdf_path:
            print("Primary click did not yield a local PDF; attempting fetch-based download fallback...")
            try:
                fetch_result = driver.execute_async_script(
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
                            console.error('Whirlpool manual fetch fallback failed:', err);
                            callback(false);
                        });
                    """,
                    file_url,
                    filename,
                )
                print(f"Fetch-based fallback triggered: {fetch_result}")
            except Exception as async_err:
                print(f"Fetch-based fallback execution failed: {async_err}")

            pdf_path = wait_for_download(download_dir, timeout=30)
            if pdf_path:
                print(f"Downloaded PDF via fetch fallback: {pdf_path}")

        current_url = driver.current_url if driver.current_url != 'about:blank' else file_url

        if not pdf_path:
            print("Whirlpool fallback did not detect a local PDF download.")

        return {
            'file_url': file_url,
            'source_url': product_url,
            'title': "Owner's Manual",
            'matched_model': model,
            'current_url': current_url,
            'local_path': pdf_path,
        }
    except Exception as err:
        print(f"Error during Whirlpool DuckDuckGo callback: {err}")
        return None

def fallback_scrape(driver, model, search_url, download_dir):
    """Fallback scraping mechanism for Whirlpool manuals."""

    # Attempt the legacy direct owners-center URL first.
    direct_result = None
    direct_url = f"https://www.whirlpool.com/owners-center-pdp.{model}.html"
    try:
        print(f"Owner's Manual link not found for {model} on search page, trying direct owners-center URL...")
        safe_driver_get(driver, direct_url)
        print(f"Navigated to direct URL: {direct_url}")

        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        print("Direct page loaded.")

        try:
            print("Searching for Owner's Manual link using data-doc-type")
            manual_link = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//div[@data-doc-type='owners-manual']//a"))
            )
            print("Found owner's manual document link.")

            file_url = manual_link.get_attribute("href")
            file_url = urljoin(direct_url, file_url)
            print(f"Found manual link: {file_url}")

            files_before = set(os.listdir(download_dir))
            driver.execute_script("arguments[0].scrollIntoView();", manual_link)
            time.sleep(0.2)
            driver.execute_script("arguments[0].click();", manual_link)

            print("Waiting for download to complete...")
            pdf_path = None
            for _ in range(5):
                time.sleep(0.2)
                files_after = set(os.listdir(download_dir))
                new_files = files_after - files_before
                if new_files:
                    new_filename = new_files.pop()
                    pdf_path = os.path.join(download_dir, new_filename)
                    break
            if not pdf_path:
                pdf_path = wait_for_download(download_dir, timeout=15)

            if pdf_path:
                print(f"Downloaded PDF: {pdf_path}")
                direct_result = {
                    'brand': 'whirlpool',
                    'model_number': model,
                    'doc_type': 'owner',
                    'title': "Owner's Manual",
                    'source_url': direct_url,
                    'file_url': file_url,
                    'local_path': pdf_path,
                }
            else:
                print("No new PDF downloaded after clicking link")
                crdownload_files = [f for f in os.listdir(download_dir) if f.endswith('.crdownload')]
                if crdownload_files:
                    print(f"Found partial download files: {crdownload_files}. Download may be slow or stuck.")

        except Exception as e:
            print(f"Error finding manual on direct page: {e}")

    except Exception as e:
        print(f"An error occurred during direct fallback for model {model}: {e}")

    if direct_result:
        return direct_result

    print(f"Direct URL fallback did not succeed for {model}; trying Whirlpool.com via DuckDuckGo...")

    fallback_url = 'whirlpool.com'
    fallback_callback = lambda d: whirlpool_duckduckgo_callback(d, model, download_dir)
    fallback_result = duckduckgo_fallback(
        driver,
        model,
        fallback_url,
        fallback_callback,
        f"\"{model}\" site:{fallback_url}",
        max_model_trim=3,
        disallowed_url_substrings=["owners-center"],
    )

    if not fallback_result:
        print(f"Whirlpool DuckDuckGo fallback failed for {model}.")
        return None

    pdf_path = fallback_result.get('local_path') or wait_for_download(download_dir, timeout=30)
    if pdf_path:
        print(f"Downloaded PDF from Whirlpool DuckDuckGo fallback: {pdf_path}")
    else:
        print("No local PDF detected after Whirlpool DuckDuckGo fallback; relying on remote file URL.")

    return {
        'brand': 'whirlpool',
        'model_number': model,
        'doc_type': 'owner',
        'title': fallback_result.get('title', "Owner's Manual"),
        'source_url': fallback_result.get('source_url', search_url),
        'file_url': fallback_result.get('file_url'),
        'local_path': pdf_path,
    }

def scrape_whirlpool_manual(model):
    """
    Scrape the owner's manual PDF for a given Whirlpool appliance model.

    Args:
        model (str): The model number (e.g., WRT311FZDW)

    Returns:
        dict: Scraped data or None if not found
    """
    search_url = f"https://www.whirlpool.com/results.html?term={model}"
    print(f"Fetching page for model {model}...")
    # Set download preferences
    temp_dir = create_temp_download_dir()
    download_dir = temp_dir
    options = get_chrome_options(download_dir)

    driver = create_chrome_driver(options=options, download_dir=download_dir)
    try:
        print(f"Navigating to: {search_url}")
        safe_driver_get(driver, search_url)
        print(f"Current URL: {driver.current_url}")

        # Wait for page to load
        print("Waiting for page elements to load...")
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "clp-item-link"))
        )
        print("Page loaded successfully.")

        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        print(f"Page title: {driver.title}")

        # Debug: find all clp-item-link elements
        all_links = soup.find_all('a', class_='clp-item-link')
        print(f"Found {len(all_links)} clp-item-link elements:")
        for i, link in enumerate(all_links):
            print(f"  {i+1}. Text: '{link.get_text(strip=True)}', Href: '{link.get('href')}'")

        # Find and click the Owner's Manual link
        try:
            owners_manual_link = EC.presence_of_element_located((By.XPATH, "//a[contains(@class, 'clp-item-link') and contains(text(), \"Owner's Manual\")]"))
            
            file_url = owners_manual_link.get_attribute("href")
            file_url = urljoin(driver.current_url, file_url)
            print(f"Found Owner's Manual link: {file_url}")

            files_before = set(os.listdir(download_dir))

            # Scroll to element and use JavaScript click to avoid interception
            driver.execute_script("arguments[0].scrollIntoView();", owners_manual_link)
            time.sleep(0.2)
            driver.execute_script("arguments[0].click();", owners_manual_link)

            # Wait for download to complete (check for new PDF files)
            print("Waiting for download to complete...")
            time.sleep(0.2)

            files_after = set(os.listdir(download_dir))
            new_files = files_after - files_before

            if new_files:
                new_filename = new_files.pop()
                pdf_path = os.path.join(download_dir, new_filename)
                print(f"Downloaded PDF: {pdf_path}")

                result = {
                    'brand': 'whirlpool',
                    'model_number': model,
                    'doc_type': 'owner',
                    'title': "Owner's Manual",
                    'source_url': search_url,
                    'file_url': file_url,
                    'local_path': pdf_path,
                }

                return result
            else:
                print("No new PDF downloaded after clicking link")
                crdownload_files = [f for f in os.listdir(download_dir) if f.endswith('.crdownload')]
                if crdownload_files:
                    print(f"Found partial download files: {crdownload_files}. Download may be slow or stuck.")
                return None

        except Exception as e:
            print(f"Error finding or clicking Owner's Manual link: {e}")
            return fallback_scrape(driver, model, search_url, download_dir)

    except Exception as e:
        print(f"An error occurred while scraping for model {model}: {e}")
        return fallback_scrape(driver, model, search_url, download_dir)
    finally:
        driver.quit()

def ingest_whirlpool_manual(result):
    from utils import validate_and_ingest_manual
    return validate_and_ingest_manual(result, False)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 whirlpool_headless_scraper.py <model_number1> <model_number2> ...")
        sys.exit(1)
    
    models = sys.argv[1:]
    for model in models:
        result = scrape_whirlpool_manual(model)
        if result:
            print("Scraping successful!")
            print(result)
            # Optionally ingest
            ingest_result = ingest_whirlpool_manual(result)
            if ingest_result:
                print(f"Ingested with ID: {ingest_result.id}")
        else:
            print("Scraping failed.")


if __name__ == "__main__":
    main()
