#!/usr/bin/env python3
"""
GE Appliance Parts Headless Scraper

Uses undetected-chromedriver for stealthy headless scraping to avoid bot detection.
Extracts owner's manual PDFs from geapplianceparts.com.

Usage: python3 ge_headless_scraper.py <model_number>

Example: python3 ge_headless_scraper.py CFE28TSHFSS
"""

import re
import sys
import time
from urllib.parse import urljoin

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup, Tag
import requests
from difflib import SequenceMatcher


def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


def scrape_ge_manual(model):
    """
    Scrape the owner's manual PDF for a given GE appliance model.

    Args:
        model (str): The model number (e.g., CFE28TSHFSS)

    Returns:
        dict: Scraped data or None if not found
    """
    url = f"https://www.geapplianceparts.com/store/parts/assembly/{model}.html"

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

        # Wait for the page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(2)

        # Get the page source and parse it
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        # Check if we landed on an error page
        error_h1 = soup.find('h1', string=re.compile(r"Uh-oh! There.s A Problem", re.IGNORECASE))
        if error_h1:
            print("Landed on an error page, performing a keyword search...")
            search_url = f"https://www.geapplianceparts.com/store/parts/KeywordSearch?q={model}"
            driver.get(search_url)
            print(f"Current URL: {driver.current_url}")

            # Wait for the search results to load and re-parse the page
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(2)
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')

            # Find all potential model links
            links = soup.find_all('a', href=re.compile(r'/store/parts/assembly/'))
            
            best_match_url = None
            highest_similarity = 0.0

            for link in links:
                link_text = link.get_text(strip=True)
                similarity = similar(model.upper(), link_text.upper())
                
                if similarity > highest_similarity:
                    highest_similarity = similarity
                    if isinstance(link, Tag) and link.get('href'):
                         best_match_url = urljoin(driver.current_url, str(link['href']))

            if highest_similarity >= 0.75 and best_match_url:
                print(f"Found a model with {highest_similarity:.2f} similarity. Navigating to: {best_match_url}")
                driver.get(best_match_url)
                print(f"Current URL: {driver.current_url}")

                # Wait for the final page to load and re-parse
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                time.sleep(2)
                page_source = driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
            else:
                print("Could not find a sufficiently similar model link in search results.")


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
                'brand': 'ge',
                'model_number': model,
                'doc_type': doc_type,
                'title': title,
                'source_url': driver.current_url,
                'file_url': pdf_url,
            })
        
        return results

    except Exception as e:
        print(f"Error scraping {model}: {e}")
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


def ingest_ge_manual(result):
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
        print("Usage: python3 ge_headless_scraper.py <model_number>")
        sys.exit(1)

    model = sys.argv[1].strip()
    if not model:
        print("Model number cannot be empty.")
        sys.exit(1)

    results = scrape_ge_manual(model)
    if results:
        print("Scraping successful!")
        for result in results:
            print(result)
            # Optionally ingest
            ingest_result = ingest_ge_manual(result)
            if ingest_result:
                print(f"Ingested with ID: {ingest_result.id}")
    else:
        print("Scraping failed.")


if __name__ == "__main__":
    main()