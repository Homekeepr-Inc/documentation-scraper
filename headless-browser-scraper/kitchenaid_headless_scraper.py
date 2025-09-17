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
import time
import os
import tempfile
import traceback
import random
from urllib.parse import urljoin

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup, Tag
import requests

# Import config for BLOB_ROOT
from app.config import DEFAULT_BLOB_ROOT


def scrape_kitchenaid_manual(model):
    """
    Scrape the owner's manual PDF for a given Kitchenaid appliance model.

    Args:
        model (str): The model number (e.g., KOES530PSS)

    Returns:
        dict: Scraped data or None if not found
    """
    url = "https://www.kitchenaid.com/owners.html"

    # Launch undetected Chrome in headless mode
    options = uc.ChromeOptions()
    # options.add_argument('--headless')
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
        driver.get(url)
        print(f"Current URL: {driver.current_url}")

        # Wait for the page to load
        WebDriverWait(driver, 1).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        # time.sleep(1)

        # Open the conversion drawer
        try:
            drawer_tab = driver.find_element(By.CSS_SELECTOR, ".conversion-drawer-tab__open-close")
            drawer_tab.click()
            print("Opened drawer")
            time.sleep(1)
        except Exception as e:
            print(f"Could not open drawer: {e}")

        # Click on the input field
        try:
            input_field = driver.find_element(By.CSS_SELECTOR, ".dpc-input")
            input_field.click()
            print("Clicked input field")
            time.sleep(0.2)
        except Exception as e:
            print(f"Could not find input field: {e}")
            return None

        # Type the model number
        input_field.send_keys(model)
        print(f"Sent keys: {model}")
        time.sleep(1)

        # Wait for the model link to appear and click it
        try:
            model_link = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.LINK_TEXT, model))
            )
            print("Found model link, clicking")
            model_link.click()
            print("Clicked model link")
            time.sleep(2)
        except Exception as e:
            print(f"Could not find model link: {e}")
            return None

        # Wait for the model page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(1)

        # Find the PDF link on the model page
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$'))
        if not pdf_links:
            print("No PDF link found on model page.")
            return None

        pdf_url = urljoin(driver.current_url, pdf_links[0]['href'])
        print(f"Found PDF URL: {pdf_url}")

        # Navigate to the PDF
        driver.get(pdf_url)
        time.sleep(random.uniform(1.13, 3.02))  # Wait for download to complete

        downloads = [f for f in os.listdir(download_dir) if f.endswith('.pdf')]
        if downloads:
            pdf_path = os.path.join(download_dir, downloads[0])
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
                'source_url': 'https://www.kitchenaid.com/owners.html',
                'file_url': pdf_path,
            }]
            return results
        else:
            print("PDF download failed.")
            return None

        # Otherwise, wait for the HTML page to load and parse for PDF links
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(2)
        except:
            print("Page did not load as expected (possibly not HTML).")
            return None

        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        # Find all PDF links
        pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$'))

        if not pdf_links:
            print("No PDF links found on the page.")
            return None

        results = []
        for pdf_link in pdf_links:
            if isinstance(pdf_link, Tag):
                href = pdf_link.get('href')
                if href:
                    pdf_url = urljoin(driver.current_url, str(href))
                else:
                    continue
            else:
                continue

            title = pdf_link.get_text(strip=True) or "Owner's Manual"

            # Determine doc_type from title
            doc_type = 'owner'
            if 'install' in title.lower():
                doc_type = 'installation'
            elif 'use and care' in title.lower():
                doc_type = 'owner'
            elif 'service' in title.lower():
                doc_type = 'service'

            print(f"Found PDF: {title}")
            print(f"URL: {pdf_url}")

            results.append({
                'brand': 'kitchenaid',
                'model_number': model,
                'doc_type': doc_type,
                'title': title,
                'source_url': driver.current_url,
                'file_url': pdf_url,
            })

        return results

    except Exception as e:
        print(f"Error scraping {model}: {e}")
        traceback.print_exc()
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
    if not result:
        return None
    # Import here to avoid circular imports
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from app.ingest import ingest_from_url
    return ingest_from_url(
        brand=result['brand'],
        model_number=result['model_number'],
        doc_type=result['doc_type'],
        title=result['title'],
        source_url=result['source_url'],
        file_url=result['file_url']
    )


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