#!/usr/bin/env python3
"""
Utility functions for headless scrapers.

This module contains reusable functions that can be used across different
headless browser scrapers, such as fallback mechanisms.
"""

import time
import random
import os
from urllib.parse import urljoin

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import requests

# Import config for BLOB_ROOT
from app.config import DEFAULT_BLOB_ROOT


def safe_driver_get(driver, url, timeout=10):
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


def duckduckgo_fallback(driver, model, host_url, scrape_callback):
    """
    Generic DuckDuckGo fallback mechanism for finding manuals when direct scraping fails.

    This function performs a DuckDuckGo search for the model number, finds a trusted link
    from the specified host, navigates to it, and then calls the provided callback function
    to perform brand-specific scraping.

    Args:
        driver: Active Selenium WebDriver instance
        model (str): The model number to search for
        host_url (str): Trusted domain to filter search results (e.g., 'lg.com/us', 'whirlpool.com')
        scrape_callback (callable): Function to call after navigating to the brand's site.
                                   Should accept the driver as parameter and return scraping result.

    Returns:
        dict: Scraped data from the callback function, or None if fallback fails
    """
    print(f"Attempting DuckDuckGo fallback for {model} on {host_url}...")

    try:
        # Navigate to DuckDuckGo search.
        search_query = f"{model} owner's manual"
        safe_driver_get(driver, f"https://duckduckgo.com/?q={search_query}")
        time.sleep(random.uniform(0.5, 1.0))

        print(f"DuckDuckGo search loaded for: {search_query}")

        # Wait for search results to appear.
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a[data-testid='result-title-a']"))
        )

        # Find the first result link that contains the trusted host.
        # DuckDuckGo uses different selectors, so we try the most common ones.
        result_links = driver.find_elements(By.CSS_SELECTOR, "a[data-testid='result-title-a'], .result__a, .result__url")

        trusted_link = None
        for link in result_links:
            href = link.get_attribute('href')
            if href and host_url in href:
                print(f"Found trusted link: {href}")
                trusted_link = link
                break

        if not trusted_link:
            print(f"No trusted link found for {host_url}")
            return None

        # Click the trusted link.
        trusted_link.click()
        time.sleep(random.uniform(0.5, 1.0))

        print(f"Navigated to: {driver.current_url}")

        # Call the brand-specific scraping callback.
        return scrape_callback(driver)

    except Exception as e:
        print(f"DuckDuckGo fallback failed: {e}")
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


def wait_for_download(download_dir, timeout=30):
    """
    Wait for a PDF download to complete in the specified directory.

    Args:
        download_dir (str): Directory to monitor for downloads
        timeout (int): Maximum time to wait in seconds

    Returns:
        str: Path to the downloaded PDF file, or None if timeout/no PDF found
    """
    import time
    start_time = time.time()

    while time.time() - start_time < timeout:
        pdf_files = [f for f in os.listdir(download_dir) if f.endswith('.pdf')]
        if pdf_files:
            # Return the most recently modified PDF.
            pdf_files.sort(key=lambda x: os.path.getmtime(os.path.join(download_dir, x)), reverse=True)
            return os.path.join(download_dir, pdf_files[0])
        time.sleep(0.5)

    return None


def ingest_manual(result):
    """
    Generic function to ingest a scraped manual result into the database.

    Args:
        result (dict): Scraped result containing brand, model_number, doc_type, title, source_url, file_url
                       Optionally local_path if downloaded locally.

    Returns:
        IngestResult: Result of the ingestion
    """
    if not result:
        return None
    # Import here to avoid circular imports
    from app.ingest import ingest_from_local_path, ingest_from_url
    if 'local_path' in result:
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