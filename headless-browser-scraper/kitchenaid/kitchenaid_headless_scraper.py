#!/usr/bin/env python3
"""
Kitchenaid Appliance Manuals Headless Scraper

Uses undetected-chromedriver for stealthy headless scraping to avoid bot detection.
Extracts owner's manual PDFs from kitchenaid.com.

Usage: python3 kitchenaid_headless_scraper.py <model_number>

Example: python3 kitchenaid_headless_scraper.py KOES530PSS
"""

import re
import sys
import os
import tempfile
import time
import traceback
from urllib.parse import urljoin

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup, Tag
import requests

# Import utility functions
sys.path.append(os.path.dirname(__file__))
from utils import safe_driver_get

# Import config for BLOB_ROOT
from app.config import DEFAULT_BLOB_ROOT


def scrape_from_page(driver, model, download_dir):
    """
    Scrape PDF from the current page.
    """
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')
    pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$'))
    if not pdf_links:
        print("No PDF link found on page.")
        return None

    pdf_url = urljoin(driver.current_url, pdf_links[0]['href'])
    print(f"Found PDF URL: {pdf_url}")

    # Navigate to the PDF
    safe_driver_get(driver, pdf_url)
    # Wait for download to complete
    WebDriverWait(driver, 30).until(
        lambda d: any(f.endswith('.pdf') for f in os.listdir(download_dir))
    )

    downloads = [f for f in os.listdir(download_dir) if f.endswith('.pdf')]
    if downloads:
        old_path = os.path.join(download_dir, downloads[0])
        # Poll until file size stabilizes to ensure download complete
        initial_size = -1
        stable_count = 0
        for _ in range(30):  # max 30 seconds
            if os.path.exists(old_path):
                size = os.path.getsize(old_path)
                if size == initial_size:
                    stable_count += 1
                    if stable_count >= 3:  # stable for 3 seconds
                        break
                else:
                    stable_count = 0
                initial_size = size
            time.sleep(1)
        else:
            print("Download did not stabilize within 30 seconds")
            return None
        new_name = f"{model}.pdf"
        new_path = os.path.join(download_dir, new_name)
        os.rename(old_path, new_path)
        pdf_path = new_path
        print(f"Downloaded PDF: {pdf_path}")

        title = "Owner's Manual"
        # Try to extract better title from URL
        if 'owners-manual' in pdf_url.lower():
            title = "Owner's Manual"
        elif 'install' in pdf_url.lower():
            title = "Installation Manual"
        elif 'service' in pdf_url.lower():
            title = "Service Manual"

        results = [{
            'brand': 'kitchenaid',
            'model_number': model,
            'doc_type': 'owner',  # Default to owner, could be refined
            'title': title,
            'source_url': driver.current_url,
            'file_url': pdf_path,
        }]
        return results
    else:
        print("PDF download failed.")
        return None


def scrape_kitchenaid_manual(model):
    """
    Scrape the owner's manual PDF for a given Kitchenaid appliance model.

    Args:
        model (str): The model number (e.g., KOES530PSS)

    Returns:
        dict: Scraped data or None if not found
    """
    url = "https://www.kitchenaid.com/owners.html"

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
        print(f"Fetching owners page for model {model}...")
        safe_driver_get(driver, url)
        print(f"Current URL: {driver.current_url}")

        # Open the conversion drawer
        try:
            drawer_tab = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".conversion-drawer-tab__open-close"))
            )
            drawer_tab.click()
            print("Opened drawer")
            # Wait for input field to be clickable after drawer opens
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".dpc-input"))
            )
        except Exception as e:
            print(f"Could not open drawer or find input field: {e}")
            return None

        # Click on the input field
        try:
            input_field = driver.find_element(By.CSS_SELECTOR, ".dpc-input")
            input_field.click()
            print("Clicked input field")
        except Exception as e:
            print(f"Could not find input field: {e}")
            return None

        # Type the model number
        input_field.send_keys(model)
        print(f"Sent keys: {model}")

        # Wait for the model link to appear and click it
        try:
            model_link = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.LINK_TEXT, model))
            )
            print("Found model link, clicking")
            model_link.click()
            print("Clicked model link")
            # Wait for the model page to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
        except Exception as e:
            print(f"Could not find model link: {e}")
            # Try fallback
            print("Trying fallback URL...")
            fallback_url = f"https://www.kitchenaid.com/owners-center-pdp.{model}.html"
            safe_driver_get(driver, fallback_url)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            result = scrape_from_page(driver, model, download_dir)
            return result

        # Try scraping from the model page
        result = scrape_from_page(driver, model, download_dir)
        if result:
            return result

        # Fallback: try direct URL
        print("Initial scrape failed, trying fallback URL...")
        fallback_url = f"https://www.kitchenaid.com/owners-center-pdp.{model}.html"
        safe_driver_get(driver, fallback_url)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        result = scrape_from_page(driver, model, download_dir)
        return result

    except Exception as e:
        print(f"Error scraping {model}: {e}")
        traceback.print_exc()
        # Try fallback on any exception
        try:
            print("Trying fallback URL due to error...")
            fallback_url = f"https://www.kitchenaid.com/owners-center-pdp.{model}.html"
            safe_driver_get(driver, fallback_url)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            result = scrape_from_page(driver, model, download_dir)
            if result:
                return result
        except Exception as e2:
            print(f"Fallback also failed: {e2}")
        return None

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


def ingest_kitchenaid_manual(result):
    from utils import ingest_manual
    return ingest_manual(result)


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 kitchenaid_headless_scraper.py <model_number>")
        sys.exit(1)

    model = sys.argv[1].strip()
    if not model:
        print("Model number cannot be empty.")
        sys.exit(1)

    results = scrape_kitchenaid_manual(model)
    if results:
        print("Scraping successful!")
        for result in results:
            print(result)
            # Optionally ingest
            ingest_result = ingest_kitchenaid_manual(result)
            if ingest_result:
                print(f"Ingested with ID: {ingest_result.id}")
    else:
        print("Scraping failed.")


if __name__ == "__main__":
    main()