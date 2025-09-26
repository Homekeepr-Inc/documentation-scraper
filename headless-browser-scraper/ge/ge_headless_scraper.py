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

# Import utility functions
import os
import sys
sys.path.append(os.path.dirname(__file__))
from utils import safe_driver_get, validate_and_ingest_manual, get_chrome_options
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
    options = get_chrome_options()

    driver = uc.Chrome(options=options)

    try:
        print(f"Fetching page for model {model}...")
        safe_driver_get(driver, url)
        print(f"Current URL: {driver.current_url}")

        # Wait for the page to load
        WebDriverWait(driver, 5).until(
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
            safe_driver_get(driver, search_url)
            print(f"Current URL: {driver.current_url}")

            # Wait for the search results to load and re-parse the page
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(2)
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')

            # Handle cookie consent if present
            try:
                driver.find_element(By.CSS_SELECTOR, ".onetrust-pc-dark-filter").click()
                time.sleep(1)
                driver.switch_to.frame(4)
                driver.find_element(By.CSS_SELECTOR, ".mat-mdc-button-touch-target").click()
                driver.switch_to.default_content()
                driver.find_element(By.ID, "onetrust-pc-btn-handler").click()
                driver.find_element(By.CSS_SELECTOR, ".save-preference-btn-handler").click()
                time.sleep(1)
            except Exception as e:
                print(f"Cookie handling skipped or failed: {e}")

            # Check for "You’re Almost There!" page
            almost_there_h1 = soup.find('h1', string="You’re Almost There!")
            if almost_there_h1:
                print("Found 'You’re Almost There!' page, looking for matching variant links.")
                # Find all assembly links
                assembly_links = soup.find_all('a', href=re.compile(r'/store/parts/assembly/'))
                prefix_len = int(len(model) * 0.6)
                model_prefix = model.upper()[:prefix_len]
                matching_link = None
                for link in assembly_links:
                    link_text = link.get_text(strip=True).upper()
                    if link_text.startswith(model_prefix):
                        matching_link = link
                        break
                if matching_link and matching_link.get('href'):
                    variant_url = urljoin(driver.current_url, matching_link['href'])
                    print(f"Using matching variant: {variant_url}")
                    safe_driver_get(driver, variant_url)
                    print(f"Navigated to variant: {driver.current_url}")
                    # Wait and re-parse
                    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                    time.sleep(2)
                    page_source = driver.page_source
                    soup = BeautifulSoup(page_source, 'html.parser')
                    # Now find Owner's Manual link on this page
                    manual_link = soup.find('a', string=lambda text: text and text.strip() == "Owner's Manual")
                    if manual_link and manual_link.get('href'):
                        manual_url = urljoin(driver.current_url, manual_link['href'])
                        print(f"Found Owner's Manual link on variant page: {manual_url}")
                        safe_driver_get(driver, manual_url)
                        print(f"Navigated to manual: {driver.current_url}")
                        # Wait and re-parse
                        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                        time.sleep(2)
                        page_source = driver.page_source
                        soup = BeautifulSoup(page_source, 'html.parser')
                    else:
                        print("No Owner's Manual link found on variant page.")
                else:
                    print(f"No variant link found with prefix match for {model}.")
            else:
                # Find the exact matching h3
                h3 = soup.find('h3', string=lambda text: text and text.strip().upper() == model.upper())
                if h3:
                    print(f"Found exact h3: '{h3.get_text(strip=True)}'")
                    parent = h3.find_parent('div')
                    if parent:
                        # Check for direct "Owner's Manual" link
                        manual_link = parent.find('a', string=lambda text: text and text.strip() == "Owner's Manual")
                        if manual_link and manual_link.get('href'):
                            manual_url = urljoin(driver.current_url, manual_link['href'])
                            print(f"Found direct Owner's Manual link: {manual_url}")
                            safe_driver_get(driver, manual_url)
                            print(f"Navigated to manual: {driver.current_url}")
                            # Wait and re-parse
                            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                            time.sleep(2)
                            page_source = driver.page_source
                            soup = BeautifulSoup(page_source, 'html.parser')
                        else:
                            # Find first assembly link
                            assembly_link = parent.find('a', href=re.compile(r'/store/parts/assembly/'))
                            if assembly_link and assembly_link.get('href'):
                                assembly_url = urljoin(driver.current_url, assembly_link['href'])
                                print(f"Using first variant: {assembly_url}")
                                safe_driver_get(driver, assembly_url)
                                print(f"Navigated to variant: {driver.current_url}")
                                # Wait and re-parse
                                WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                                time.sleep(2)
                                page_source = driver.page_source
                                soup = BeautifulSoup(page_source, 'html.parser')
                                # Now find Owner's Manual link on this page
                                manual_link = soup.find('a', string=lambda text: text and text.strip() == "Owner's Manual")
                                if manual_link and manual_link.get('href'):
                                    manual_url = urljoin(driver.current_url, manual_link['href'])
                                    print(f"Found Owner's Manual link on variant page: {manual_url}")
                                    safe_driver_get(driver, manual_url)
                                    print(f"Navigated to manual: {driver.current_url}")
                                    # Wait and re-parse
                                    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                                    time.sleep(2)
                                    page_source = driver.page_source
                                    soup = BeautifulSoup(page_source, 'html.parser')
                                else:
                                    print("No Owner's Manual link found on variant page.")
                            else:
                                print("No assembly link found in the h3 section.")
                    else:
                        print("No parent div found for h3.")
                else:
                    print(f"No exact h3 match found for {model}.")


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
    from utils import validate_and_ingest_manual
    return validate_and_ingest_manual(result, False)


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