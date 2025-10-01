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
from utils import safe_driver_get, wait_for_download, validate_pdf_file, validate_and_ingest_manual, create_temp_download_dir, cleanup_temp_dir, get_chrome_options, create_chrome_driver


def fallback_scrape(model, driver, temp_dir):
    """
    Fallback scraping mechanism for Samsung manuals.
    """
    download_dir = temp_dir
    try:
        print(f"Primary scraping failed for {model}, trying fallback...")
        # Check if model has "/XX" suffix, strip it and add "-xx"
        original_model = model
        normalized_model = model.replace('/', '_')
        if '/' in model:
            parts = model.split('/')
            if len(parts) == 2 and len(parts[1]) == 2:
                stripped_model = parts[0]
                suffix = parts[1].lower()
                fallback_url = f"https://samsungparts.com/products/{stripped_model}-{suffix}"
            else:
                fallback_url = f"https://samsungparts.com/products/{model}"
        else:
            fallback_url = f"https://samsungparts.com/products/{model}"
        safe_driver_get(driver, fallback_url)
        print(f"Navigated to fallback URL: {fallback_url}")

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".bmpg-ownersManualLink"))
        )


        owners_manual_link = driver.find_element(By.CSS_SELECTOR, ".bmpg-ownersManualLink a")
        pdf_url = owners_manual_link.get_attribute("href")
        if not pdf_url or not isinstance(pdf_url, str) or not pdf_url.startswith('http'):
            print("Invalid or missing PDF URL")
            return None
        title = f"Samsung {original_model} manual"

        # Navigate to the PDF URL to trigger download via browser
        safe_driver_get(driver, pdf_url)

        # Wait for download to complete
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


def scrape_samsung_manual(model, driver, temp_dir):
    """
    Scrape the owner's manual PDF for a given Samsung appliance model.

    Args:
        model (str): The model number (e.g., RF29DB9900QDAA)
        driver: Selenium WebDriver instance
        temp_dir (str): Temporary directory for downloads

    Returns:
        dict: Scraped data or None if not found
    """
    # Normalize model by replacing "/" with "_"
    normalized_model = model.replace('/', '_')
    download_dir = temp_dir

    # Prepare search term and model code
    if '/' in model:
        search_term = model.split('/')[0]
        model_code = model.replace('/', '').upper()
    else:
        search_term = model
        model_code = model

    url = "https://www.samsung.com/latin_en/support/user-manuals-and-guide/"

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
        input_field.send_keys(search_term)

        # Find submit button
        submit_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".sud13-search__input-btn--search"))
        )
        submit_button.click()

        # Wait for search results and try to find the model link
        model_link = None
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, f'a[data-modelcode="{model_code}"]'))
            )
            model_link = driver.find_element(By.CSS_SELECTOR, f'a[data-modelcode="{model_code}"]')
        except:
            # If not found, try with model without suffix
            if '/' in model:
                alt_model_code = model.split('/')[0]
                try:
                    WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, f'a[data-modelcode="{alt_model_code}"]'))
                    )
                    model_link = driver.find_element(By.CSS_SELECTOR, f'a[data-modelcode="{alt_model_code}"]')
                except:
                    pass

        if model_link is None:
            raise Exception("Model link not found with any attempted model code")

        # Click the model link
        model_link.click()

        # Wait for the model page to load
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".sud13-select-option:nth-child(1) .sud13-select-option__item-label"))
        )

        # Click the first option (likely language)
        option = driver.find_element(By.CSS_SELECTOR, ".sud13-select-option:nth-child(1) .sud13-select-option__item-label")
        option.click()

        # Scroll a bit
        driver.execute_script("window.scrollTo(0,320)")

        # Wait for download link
        WebDriverWait(driver, 5).until(
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
        return fallback_scrape(model, driver, temp_dir)


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
    # Samsung does not usually specify specific model names in their PDFs.
    # Because of this, we don't validate the content of the PDF contains the model number provided in the request as it will usually fail.
    return validate_and_ingest_manual(result, False)


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 samsung_headless_scraper.py <model_number>")
        sys.exit(1)

    model = sys.argv[1].strip()
    if not model:
        print("Model number cannot be empty.")
        sys.exit(1)

    # For standalone run, create a driver
    temp_dir = create_temp_download_dir()
    options = get_chrome_options(temp_dir)
    driver = create_chrome_driver(options=options)
    try:
        results = scrape_samsung_manual(model, driver, temp_dir)
    finally:
        driver.quit()
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

