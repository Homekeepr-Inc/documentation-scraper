#!/usr/bin/env python3
"""
A.O. Smith Appliance Manuals Headless Scraper

Uses undetected-chromedriver for stealthy headless scraping to avoid bot detection.
Extracts owner's manual PDFs from aosmithatlowes.com.
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

# Add paths to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))  # project root
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))  # headless-browser-scraper

# Import utility functions
from utils import safe_driver_get, wait_for_download, validate_pdf_file, validate_and_ingest_manual, create_temp_download_dir, cleanup_temp_dir, duckduckgo_fallback


def aosmith_scrape_callback(driver):
    """
    Callback function for A.O. Smith scraping after navigating to the product page via DuckDuckGo.
    """
    try:
        # Scroll down
        driver.execute_script("window.scrollTo(0,192)")

        # Click the tabcordion section for "Use & Care Instructions"
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".tabcordion-tabsection.tabcordion-tabsection-5"))
        )
        tab_section = driver.find_element(By.CSS_SELECTOR, ".tabcordion-tabsection.tabcordion-tabsection-5")
        tab_section.click()

        # Wait for the content to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".tabcordion-content.tabcordion-content-5"))
        )

        # Find the Owners Manual link
        content_div = driver.find_element(By.CSS_SELECTOR, ".tabcordion-content.tabcordion-content-5")
        manual_link = content_div.find_element(By.CSS_SELECTOR, "a[title*='Owners Manual']")
        file_url = manual_link.get_attribute("href")
        if not file_url.startswith('http'):
            from urllib.parse import urljoin
            file_url = urljoin(driver.current_url, file_url)
        title = manual_link.get_attribute("title") or "A.O. Smith Owners Manual"

        # Navigate to the PDF URL to download
        safe_driver_get(driver, file_url)

        return {
            'file_url': file_url,
            'title': title,
            'source_url': driver.current_url,
        }

    except Exception as e:
        print(f"Error in A.O. Smith callback: {e}")
        return None


def scrape_aosmith_manual(model):
    """
    Scrape the owner's manual PDF for a given A.O. Smith appliance model using DuckDuckGo fallback.

    Args:
        model (str): The model number (e.g., E6-50H45DV)

    Returns:
        dict: Scraped data or None if not found
    """
    # Normalize model by replacing "/" with "_"
    normalized_model = model.replace('/', '_')

    # Launch undetected Chrome
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    # Set download preferences
    temp_dir = create_temp_download_dir()
    download_dir = temp_dir
    options.add_experimental_option("prefs", {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True
    })

    driver = uc.Chrome(options=options)

    try:
        print(f"Attempting DuckDuckGo fallback for A.O. Smith model {model}...")

        # Use duckduckgo_fallback as primary
        result = duckduckgo_fallback(driver, model, 'aosmithatlowes.com', aosmith_scrape_callback)

        if result:
            # Wait for download after callback
            pdf_path = wait_for_download(download_dir, timeout=30)

            if pdf_path and validate_pdf_file(pdf_path):
                print(f"Downloaded and validated PDF: {pdf_path}")
                return {
                    'brand': 'aosmith',
                    'model_number': normalized_model,
                    'doc_type': 'owner',
                    'title': result['title'],
                    'source_url': result['source_url'],
                    'file_url': result['file_url'],
                    'local_path': pdf_path,
                }
            else:
                print("No valid PDF downloaded.")
                return None
        else:
            print("DuckDuckGo fallback failed.")
            return None

    except Exception as e:
        print(f"An error occurred during scraping for A.O. Smith {model}: {e}")
        return None

    finally:
        driver.quit()


def ingest_aosmith_manual(result):
    from utils import validate_and_ingest_manual
    # A.O. Smith PDFs may not contain exact model numbers, so disable content validation
    return validate_and_ingest_manual(result, False)


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 aosmith_headless_scraper.py <model_number>")
        sys.exit(1)

    model = sys.argv[1].strip()
    if not model:
        print("Model number cannot be empty.")
        sys.exit(1)

    results = scrape_aosmith_manual(model)
    if results:
        print("Scraping successful!")
        print(results)
        # Optionally ingest
        ingest_result = ingest_aosmith_manual(results)
        if ingest_result:
            print(f"Ingested with ID: {ingest_result.id}")
    else:
        print("Scraping failed.")


if __name__ == "__main__":
    main()