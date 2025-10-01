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
from urllib.parse import urljoin

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import requests

# Import utility functions
sys.path.append(os.path.dirname(__file__))
from utils import safe_driver_get, validate_and_ingest_manual, create_temp_download_dir, cleanup_temp_dir, get_chrome_options, create_chrome_driver

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.config import DEFAULT_BLOB_ROOT

def fallback_scrape(driver, model, search_url, download_dir):
    """
    Fallback scraping mechanism for Whirlpool manuals.
    """
    try:
        print(f"Owner's Manual link not found for {model} on search page, trying direct owners-center URL...")
        # Try direct owners-center URL
        direct_url = f"https://www.whirlpool.com/owners-center-pdp.{model}.html"
        safe_driver_get(driver, direct_url)
        print(f"Navigated to direct URL: {direct_url}")

        # Wait for page to load
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        print("Direct page loaded.")

        # Find and click the owner's manual document link
        try:
            print("Searching for Owner's Manual link using data-doc-type")
            # Look for the div with data-doc-type='owners-manual' and get the a inside it
            manual_link = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.XPATH, "//div[@data-doc-type='owners-manual']//a"))
            )
            print("Found owner's manual document link.")

            file_url = manual_link.get_attribute("href")
            file_url = urljoin(direct_url, file_url)
            print(f"Found manual link: {file_url}")

            files_before = set(os.listdir(download_dir))

            # Scroll to element and use JavaScript click to avoid interception
            driver.execute_script("arguments[0].scrollIntoView();", manual_link)
            time.sleep(0.2)
            driver.execute_script("arguments[0].click();", manual_link)

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
                    'source_url': direct_url,
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
            print(f"Error finding manual on direct page: {e}")
            print(f"Direct URL fallback also failed for {model}")
            return None

    except Exception as e:
        print(f"An error occurred during fallback scraping for model {model}: {e}")
        return None

def scrape_whirlpool_manual(model, driver, temp_dir):
    """
    Scrape the owner's manual PDF for a given Whirlpool appliance model.

    Args:
        model (str): The model number (e.g., WRT311FZDW)
        driver: Selenium WebDriver instance
        temp_dir (str): Temporary directory for downloads

    Returns:
        dict: Scraped data or None if not found
    """
    search_url = f"https://www.whirlpool.com/results.html?term={model}"
    print(f"Fetching page for model {model}...")
    download_dir = temp_dir

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

def ingest_whirlpool_manual(result):
    from utils import validate_and_ingest_manual
    return validate_and_ingest_manual(result, False)


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 whirlpool_headless_scraper.py <model_number1> <model_number2> ...")
        sys.exit(1)
    
    models = sys.argv[1:]
    for model in models:
        # For standalone run, create a driver
        temp_dir = create_temp_download_dir()
        options = get_chrome_options(temp_dir)
        driver = create_chrome_driver(options=options)
        try:
            result = scrape_whirlpool_manual(model, driver, temp_dir)
        finally:
            driver.quit()
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
