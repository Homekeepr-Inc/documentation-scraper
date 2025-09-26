#!/usr/bin/env python3
"""
Frigidaire Appliance Manuals Headless Scraper

Uses undetected-chromedriver for stealthy headless scraping to avoid bot detection.
Extracts owner's manual PDFs from frigidaire.com.

Usage: python3 frigidaire_headless_scraper.py <model_number>

Example: python3 frigidaire_headless_scraper.py FPFU19F8WF
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
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup, Tag
import requests

# Import config for BLOB_ROOT
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from app.config import DEFAULT_BLOB_ROOT

# Import utility functions
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils import duckduckgo_fallback, validate_pdf_file, wait_for_download, safe_driver_get, validate_and_ingest_manual, get_chrome_options


def parse_manual_links(driver, model):
    """
    Parse manual links from the current Frigidaire page.

    Args:
        driver: Active Selenium WebDriver instance
        model: The model number being scraped

    Returns:
        dict: Scraped data or None if not found
    """
    try:
        print("Looking for manual links on Frigidaire page...")
        print(f"Current URL: {driver.current_url}")

        # Wait for page to load
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Wait for manuals section to load
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".manuals"))
            )
        except:
            print("Manuals section not found, waiting additional time...")
            time.sleep(5)

        # Scroll to load lazy content
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        # Get page source and parse
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        # Debug: print all links on the page
        all_links = soup.find_all('a', href=True)
        print(f"Found {len(all_links)} links on the page:")
        for i, link in enumerate(all_links[:20]):  # Show first 20 links
            href = link.get('href')
            text = link.get_text(strip=True)
            print(f"  {i+1}. {text} -> {href}")

        # Look for the specific selectors based on the actual HTML structure
        manual_selectors = [
            '.mannual-name',  # The actual class used on the manual links
            '.manuals a',     # Links within the manuals container
            'a[href*=".pdf"]', # Any PDF links
            'a[href*="guide"]', # Links containing "guide"
            'a[href*="manual"]', # Links containing "manual"
            'a[href*="electroluxmedia.com"]'  # PDFs hosted on Electrolux media
        ]

        # Collect all potential owner's manuals
        owners_manuals = []

        for selector in manual_selectors:
            try:
                elements = soup.select(selector)
                print(f"Selector '{selector}' found {len(elements)} elements")
                for element in elements:
                    href = element.get('href')
                    text = element.get_text(strip=True)
                    if href and '.pdf' in href.lower():
                        # Check if this is an owner's manual (prioritize these)
                        is_owners_manual = any(keyword in text.lower() or keyword in href.lower()
                                              for keyword in ['owner', 'complete owner', 'user guide', 'operating instructions'])

                        pdf_url = urljoin(driver.current_url, href)
                        title = text or "Manual"

                        owners_manuals.append({
                            'url': pdf_url,
                            'title': title,
                            'is_owners_manual': is_owners_manual,
                            'text': text
                        })
            except Exception as e:
                print(f"Error with selector {selector}: {e}")
                continue

        # Prioritize owner's manuals over other documents
        if owners_manuals:
            # Sort by priority: owner's manuals first, then by title
            owners_manuals.sort(key=lambda x: (not x['is_owners_manual'], x['title']))

            # Take the highest priority manual
            selected_manual = owners_manuals[0]
            pdf_url = selected_manual['url']
            title = selected_manual['title']

            print(f"Selected manual: {title} -> {pdf_url}")

            # Download and validate PDF
            try:
                response = requests.get(pdf_url, allow_redirects=True)
                response.raise_for_status()
                content = response.content
                if not content.startswith(b'%PDF-'):
                    print(f"File is not a PDF. First bytes: {content[:10]}")
                    return None
                print("Validated as PDF.")
            except Exception as e:
                print(f"Error validating PDF: {e}")
                return None

            return {
                'brand': 'frigidaire',
                'model_number': model,
                'doc_type': 'owner',
                'title': title,
                'source_url': driver.current_url,
                'file_url': pdf_url,
            }

        print("No manual links found on the page")
        return None

    except Exception as e:
        print(f"Error parsing manual links: {e}")
        return None


def scrape_frigidaire_manual(model):
    """
    Scrape the owner's manual PDF for a given Frigidaire appliance model.

    Args:
        model (str): The model number (e.g., FPFU19F8WF)

    Returns:
        dict: Scraped data or None if not found
    """
    # Try direct URL first (from DuckDuckGo fallback pattern)
    direct_url = f"https://www.frigidaire.com/en/p/owner-center/product-support/{model}"

    # Launch undetected Chrome
    # Set download preferences
    download_dir = os.path.abspath(DEFAULT_BLOB_ROOT)
    os.makedirs(download_dir, exist_ok=True)
    options = get_chrome_options(download_dir)

    driver = uc.Chrome(options=options)

    try:
        print(f"Trying direct URL for model {model}...")
        safe_driver_get(driver, direct_url)
        print(f"Current URL after navigation: {driver.current_url}")

        # Wait for page to load
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Wait for manuals section to load
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".manuals"))
            )
        except:
            print("Manuals section not found, waiting additional time...")
            time.sleep(5)

        # Scroll to load lazy content
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        print(f"Current URL after page load: {driver.current_url}")
        print(f"Looking for 'owner-center': {'owner-center' in driver.current_url}")
        print(f"Looking for model '{model}': {model in driver.current_url}")

        # Check if we got a valid product page (look for model in URL)
        if model in driver.current_url:
            print("Direct URL worked (found model in URL), looking for manual links...")

            result = parse_manual_links(driver, model)
            if result:
                return result

            print("No manual links found on direct page")
            # Try DuckDuckGo fallback before giving up
            print("Attempting DuckDuckGo fallback...")
            fallback_result = duckduckgo_fallback(driver, model, "frigidaire.com", lambda d: parse_manual_links(d, model))
            if fallback_result:
                return fallback_result
            return None
        else:
            print("Direct URL didn't work, trying original search approach...")

        # Original search approach
        print("Trying original search approach...")
        search_url = "https://www.frigidaire.com/en/product-support"
        safe_driver_get(driver, search_url)
        print(f"Search page URL: {driver.current_url}")

        # Wait for page to load
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Click search input
        search_input = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".form-control"))
        )
        search_input.click()

        # Type model number
        search_input.clear()
        search_input.send_keys(model)

        # Click search button
        search_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".fa"))
        )
        search_button.click()

        # Mouse over "Register Your Product" to trigger any JS
        try:
            register_link = driver.find_element(By.LINK_TEXT, "Register Your Product")
            actions = ActionChains(driver)
            actions.move_to_element(register_link).perform()
            # Mouse out
            body = driver.find_element(By.TAG_NAME, "body")
            actions.move_to_element(body).perform()
        except Exception as e:
            print(f"Mouse over/out failed: {e}")

        # Click product image
        try:
            product_image = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".cx-product-image > img"))
            )
            # Use JavaScript click to avoid interception
            driver.execute_script("arguments[0].scrollIntoView();", product_image)
            driver.execute_script("arguments[0].click();", product_image)
        except Exception as e:
            print(f"Error clicking product image: {e}")
            return None

        # Scroll a bit
        driver.execute_script("window.scrollTo(0,2)")
        driver.execute_script("window.scrollTo(0,816)")

        # Close modal if present
        try:
            close_modal = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "close-modal123"))
            )
            close_modal.click()
        except Exception as e:
            print(f"No modal to close or close failed: {e}")

        # Click "Complete Owner's Guide"
        owners_guide_link = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Complete Owner's Guide"))
        )

        # Store current window handles
        current_handles = driver.window_handles

        # Click the link (opens in new window/tab)
        owners_guide_link.click()

        # Switch to new window
        new_handles = driver.window_handles
        if len(new_handles) > len(current_handles):
            new_window = set(new_handles).difference(set(current_handles)).pop()
            driver.switch_to.window(new_window)

            # Get the PDF URL from current page
            current_url = driver.current_url
            if current_url.endswith('.pdf') or '.pdf' in current_url:
                pdf_url = current_url
                title = "Complete Owner's Guide"
                doc_type = 'owner'
                print(f"Found PDF: {title}")
                print(f"URL: {pdf_url}")

                # Download and validate PDF
                try:
                    response = requests.get(pdf_url, allow_redirects=True)
                    response.raise_for_status()
                    content = response.content
                    if not content.startswith(b'%PDF-'):
                        print(f"File is not a PDF. First bytes: {content[:10]}")
                        return None
                    print("Validated as PDF.")
                except Exception as e:
                    print(f"Error validating PDF: {e}")
                    return None

                return {
                    'brand': 'frigidaire',
                    'model_number': model,
                    'doc_type': doc_type,
                    'title': title,
                    'source_url': driver.current_url,
                    'file_url': pdf_url,
                }
            else:
                print("New window did not contain a PDF URL")
                return None
        else:
            print("No new window opened for owner's guide")
            return None

    except Exception as e:
        print(f"Direct URL approach failed for {model}: {e}")
        # Try DuckDuckGo fallback
        return duckduckgo_fallback(driver, model, "frigidaire.com", lambda d: parse_manual_links(d, model))

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


def ingest_frigidaire_manual(result):
    return validate_and_ingest_manual(result, False)


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 frigidaire_headless_scraper.py <model_number>")
        sys.exit(1)

    model = sys.argv[1].strip()
    if not model:
        print("Model number cannot be empty.")
        sys.exit(1)

    result = scrape_frigidaire_manual(model)
    if result:
        print("Scraping successful!")
        print(result)
        # Optionally ingest
        ingest_result = ingest_frigidaire_manual(result)
        if ingest_result:
            print(f"Ingested with ID: {ingest_result.id}")
    else:
        print("Scraping failed.")


if __name__ == "__main__":
    main()