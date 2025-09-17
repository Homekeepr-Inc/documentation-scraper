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

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.ingest import ingest_from_url
from app.config import DEFAULT_BLOB_ROOT

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
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-popup-blocking')
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
        print(f"Navigating to: {search_url}")
        driver.get(search_url)
        print(f"Current URL: {driver.current_url}")

        # Wait for page to load
        print("Waiting for page elements to load...")
        WebDriverWait(driver, 10).until(
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
            owners_manual_link = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//a[contains(@class, 'clp-item-link') and contains(text(), \"Owner's Manual\")]"))
            )
            print("Found Owner's Manual link, clicking...")

            # Scroll to element and use JavaScript click to avoid interception
            driver.execute_script("arguments[0].scrollIntoView();", owners_manual_link)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", owners_manual_link)

            # Wait for download to complete (check for new PDF files)
            print("Waiting for download to complete...")
            time.sleep(random.uniform(2.0, 4.0))  # Wait a bit for download to start

            # Check for downloaded PDF
            downloads = [f for f in os.listdir(download_dir) if f.endswith('.pdf')]
            if downloads:
                pdf_path = os.path.join(download_dir, downloads[-1])  # Get the most recent PDF
                print(f"Downloaded PDF: {pdf_path}")

                # Validate PDF
                try:
                    with open(pdf_path, 'rb') as f:
                        content = f.read()
                    if not content.startswith(b'%PDF-'):
                        print(f"File is not a PDF. First bytes: {content[:10]}")
                        return None
                    print("Validated as PDF.")
                except Exception as e:
                    print(f"Error validating PDF: {e}")
                    return None

                result = {
                    'brand': 'whirlpool',
                    'model_number': model,
                    'doc_type': 'owner',
                    'title': "Owner's Manual",
                    'source_url': search_url,
                    'file_url': pdf_path,  # Local file path
                }

                ingest_from_url(
                    brand=result['brand'],
                    model_number=result['model_number'],
                    doc_type=result['doc_type'],
                    title=result['title'],
                    source_url=result['source_url'],
                    file_url=result['file_url']
                )

                return result
            else:
                print("No PDF downloaded after clicking link")
                return None

        except Exception as e:
            print(f"Error finding or clicking Owner's Manual link: {e}")
            return None

    except Exception as e:
        print(f"An error occurred while scraping for model {model}: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        driver.quit()

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 whirlpool_headless_scraper.py <model_number1> <model_number2> ...")
        sys.exit(1)
    
    models = sys.argv[1:]
    for model in models:
        scrape_whirlpool_manual(model)

if __name__ == "__main__":
    main()
