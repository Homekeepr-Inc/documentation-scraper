#!/usr/bin/env python3
"""
LG Appliance Manuals Headless Scraper

Uses undetected-chromedriver for stealthy headless scraping to avoid bot detection.
Extracts owner's manual PDFs from lg.com.

Usage: python3 lg_scraper.py <model_number1> <model_number2> ...

Example: python3 lg_scraper.py LMXS28626S CFE28TSHFSS
"""

import re
import sys
import time
import queue
import threading
from urllib.parse import urljoin

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup, Tag
import requests

# Global queue and lock for single-instance control
job_queue = queue.Queue()
scraper_lock = threading.Lock()

def scrape_lg_manual(model):
    """
    Scrape the owner's manual PDF for a given LG appliance model.

    Args:
        model (str): The model number (e.g., LMXS28626S)

    Returns:
        dict: Scraped data or None if not found
    """
    url = f"https://www.lg.com/ca_en/support/product-support/?csSalesCode={model}"

    # Launch undetected Chrome in headless mode
    options = uc.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    driver = uc.Chrome(options=options)

    try:
        print(f"Fetching page for model {model}...")
        driver.get(url)
        print(f"Current URL: {driver.current_url}")

        # Wait for JS to render (5 seconds)
        time.sleep(5)

        # Get the page source and parse it
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        # Check for manualList div
        manual_list = soup.find('div', class_='manualList')
        if not manual_list or not isinstance(manual_list, Tag):
            print("No manual list found on the page.")
            return None

        # Find download button within manualList
        download_button = manual_list.find('div', class_='c-resources__item--download-button')
        if not download_button or not isinstance(download_button, Tag):
            print("No download button found.")
            return None

        download_link = download_button.find('a')
        if not download_link or not isinstance(download_link, Tag) or not download_link.get('href'):
            print("No valid download link found.")
            return None

        pdf_url = urljoin(driver.current_url, str(download_link['href']))
        title = download_link.get_text(strip=True) or "Owner's Manual"

        # Determine doc_type from title
        doc_type = 'owner'
        if 'install' in title.lower():
            doc_type = 'installation'
        elif 'service' in title.lower():
            doc_type = 'service'

        print(f"Found PDF: {title}")
        print(f"URL: {pdf_url}")

        # Download and validate PDF
        try:
            response = requests.get(pdf_url, allow_redirects=True)
            response.raise_for_status()
            content = response.content
            if not content.startswith(b'%PDF-'):
                print(f"Downloaded file is not a PDF. First bytes: {content[:10]}")
                return None
            print("Validated as PDF.")
        except Exception as e:
            print(f"Error validating PDF: {e}")
            return None

        return {
            'brand': 'lg',
            'model_number': model,
            'doc_type': doc_type,
            'title': title,
            'source_url': url,
            'file_url': pdf_url,
        }

    except Exception as e:
        print(f"Error scraping {model}: {e}")
        return None

    finally:
        driver.quit()

def worker():
    """Worker thread to process jobs from the queue."""
    while True:
        try:
            model = job_queue.get(timeout=1)  # Wait for a job
        except queue.Empty:
            break  # No more jobs

        with scraper_lock:  # Ensure only one instance runs at a time
            print(f"Starting scrape for {model}")
            result = scrape_lg_manual(model)
            if result:
                print("Scraping successful!")
                print(result)
                # Optionally ingest
                ingest_result = ingest_lg_manual(result)
                if ingest_result:
                    print(f"Ingested with ID: {ingest_result.id}")
            else:
                print("Scraping failed.")
        job_queue.task_done()

def enqueue_models(models):
    """Enqueue model numbers into the job queue."""
    for model in models:
        job_queue.put(model.strip())

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

def ingest_lg_manual(result):
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
    if len(sys.argv) < 2:
        print("Usage: python3 lg_scraper.py <model_number1> <model_number2> ...")
        sys.exit(1)

    models = sys.argv[1:]
    if not models or any(not model.strip() for model in models):
        print("Model numbers cannot be empty.")
        sys.exit(1)

    # Enqueue models
    enqueue_models(models)

    # Start worker thread
    worker_thread = threading.Thread(target=worker)
    worker_thread.start()

    # Wait for all jobs to complete
    job_queue.join()
    worker_thread.join()

    print("All jobs completed.")


if __name__ == "__main__":
    main()