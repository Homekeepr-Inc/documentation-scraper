#!/usr/bin/env python3
"""
Samsung Appliance Manuals Headless Scraper

Uses undetected-chromedriver for stealthy headless scraping to avoid bot detection.
Extracts owner's manual PDFs from samsung.com.

Usage: python3 samsung_headless_scraper.py <model_number>

Example: python3 samsung_headless_scraper.py RF29DB9900QDAA
"""

import re
import sys
import os
import time
import random
from urllib.parse import urljoin

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from bs4 import BeautifulSoup, Tag
import requests

# Add project root to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import config for BLOB_ROOT
from app.config import DEFAULT_BLOB_ROOT

# Import utility functions
from utils import safe_driver_get, wait_for_download, validate_pdf_file, validate_and_ingest_manual


# Was having issues re-using the main Selenium driver during fallbacks, so we create a new one here.
def fallback_scrape(model):
    """
    Fallback scraping mechanism for Samsung manuals.
    """
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    # Set download preferences
    download_dir = os.path.abspath(DEFAULT_BLOB_ROOT)
    os.makedirs(download_dir, exist_ok=True)
    options.add_experimental_option("prefs", {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True
    })

    driver = uc.Chrome(options=options)

    try:
        print(f"Primary scraping failed for {model}, trying fallback...")
        # Check if model ends with "/AA" (case insensitive), strip it and add "-aa"
        original_model = model
        normalized_model = model.replace('/', '_')
        if model.upper().endswith("/AA"):
            stripped_model = model[:-3]  # Strip "/AA"
            fallback_url = f"https://samsungparts.com/products/{stripped_model}-aa"
        else:
            stripped_model = model
            fallback_url = f"https://samsungparts.com/products/{model}"
        safe_driver_get(driver, fallback_url)
        print(f"Navigated to fallback URL: {fallback_url}")

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".bmpg-ownersManualLink"))
        )

        # Handle cookie consent
        try:
            reject_button = driver.find_element(By.ID, "onetrust-reject-all-handler")
            reject_button.click()
        except Exception:
            pass  # Ignore if not present

        owners_manual_link = driver.find_element(By.CSS_SELECTOR, ".bmpg-ownersManualLink a")
        pdf_url = owners_manual_link.get_attribute("href")
        if not pdf_url or not isinstance(pdf_url, str) or not pdf_url.startswith('http'):
            print("Invalid or missing PDF URL")
            return None
        title = f"Samsung {original_model} manual"

        # Navigate to the PDF URL directly
        safe_driver_get(driver, pdf_url)

        # Wait for download to start
        download_dir = os.path.abspath(DEFAULT_BLOB_ROOT)
        pdf_path = wait_for_download(download_dir, timeout=30)

        if pdf_path and validate_pdf_file(pdf_path):
            print(f"Downloaded and validated PDF from fallback: {pdf_path}")
            return {
                'brand': 'samsung',
                'model_number': normalized_model,
                'doc_type': 'owner',
                'title': title,
                'source_url': driver.current_url,
                'file_url': pdf_url,
                'local_path': pdf_path,
            }
        else:
            print("No valid PDF downloaded from fallback.")
            return None

    except Exception as e:
        print(f"An error occurred during fallback scraping for model {original_model}: {e}")
        return None
    finally:
        driver.quit()


def scrape_samsung_manual(model):
    """
    Scrape the owner's manual PDF for a given Samsung appliance model.

    Args:
        model (str): The model number (e.g., RF29DB9900QDAA)

    Returns:
        dict: Scraped data or None if not found
    """
    # Normalize model by replacing "/" with "_"
    normalized_model = model.replace('/', '_')

    url = "https://www.samsung.com/latin_en/support/user-manuals-and-guide/"

    # Launch undetected Chrome
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    # Set download preferences
    download_dir = os.path.abspath(DEFAULT_BLOB_ROOT)
    os.makedirs(download_dir, exist_ok=True)
    options.add_experimental_option("prefs", {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True
    })

    driver = uc.Chrome(options=options)

    try:
        print(f"Fetching page for model {model}...")
        safe_driver_get(driver, url)
        print(f"Current URL: {driver.current_url}")

        # Wait for page to load
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Click the hint to activate
        hint = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".text-field-v2__hint"))
        )
        hint.click()

        # Wait for search input
        input_field = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "sud13-code-search-input"))
        )
        input_field.click()
        input_field.send_keys(normalized_model)

        # Find submit button
        submit_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".sud13-search__input-btn--search"))
        )
        submit_button.click()

        # Wait for search results
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, f'a[data-modelcode="{normalized_model}"]'))
        )

        # Click the model link
        model_link = driver.find_element(By.CSS_SELECTOR, f'a[data-modelcode="{normalized_model}"]')
        model_link.click()

        # Wait for the model page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".sud13-select-option:nth-child(1) .sud13-select-option__item-label"))
        )

        # Click the first option (likely language)
        option = driver.find_element(By.CSS_SELECTOR, ".sud13-select-option:nth-child(1) .sud13-select-option__item-label")
        option.click()

        # Scroll a bit
        driver.execute_script("window.scrollTo(0,320)")

        # Wait for download link
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.LINK_TEXT, "Download"))
        )

        # Get the download link
        download_link = driver.find_element(By.LINK_TEXT, "Download")
        file_url = download_link.get_attribute("href")
        title = f"Samsung {model} manual"

        # Click to download
        download_link.click()

        # Wait for download to complete
        print("Waiting for download...")
        pdf_path = wait_for_download(download_dir, timeout=30)

        if pdf_path and validate_pdf_file(pdf_path):
            print(f"Downloaded and validated PDF: {pdf_path}")
            return {
                'brand': 'samsung',
                'model_number': normalized_model,
                'doc_type': 'owner',  # or infer from URL
                'title': title,
                'source_url': driver.current_url,
                'file_url': file_url,
                'local_path': pdf_path,
            }
        else:
            print("No valid PDF downloaded.")
            return None

    except Exception as e:
        print(f"Primary scraping for Samsung {model} failed: {e}")
        # On failure, try the fallback scraper
        return fallback_scrape(model)

    finally:
        driver.quit()


def download_file(url, filename):
    """Download a file from URL to local filename."""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Downloaded to {filename}")
    except Exception as e:
        print(f"Error downloading {url}: {e}")


def ingest_samsung_manual(result):
    from utils import validate_and_ingest_manual
    return validate_and_ingest_manual(result)


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 samsung_headless_scraper.py <model_number>")
        sys.exit(1)

    model = sys.argv[1].strip()
    if not model:
        print("Model number cannot be empty.")
        sys.exit(1)

    results = scrape_samsung_manual(model)
    if results:
        print("Scraping successful!")
        for result in [results]:
            print(result)
            # Optionally ingest
            ingest_result = ingest_samsung_manual(result)
            if ingest_result:
                print(f"Ingested with ID: {ingest_result.id}")
    else:
        print("Scraping failed.")


if __name__ == "__main__":
    main()

