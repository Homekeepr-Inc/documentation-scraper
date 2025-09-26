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
from utils import safe_driver_get, wait_for_download, validate_pdf_file, validate_and_ingest_manual, create_temp_download_dir, cleanup_temp_dir, duckduckgo_fallback, get_chrome_options


def aosmith_scrape_callback(driver):
    """
    Callback function for A.O. Smith scraping on aosmithatlowes.com after navigating to the product page via DuckDuckGo.
    """
    try:
        # Scroll down
        driver.execute_script("window.scrollTo(0,192)")

        # Find the Owners Manual link directly
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a[title*='Owners Manual']"))
        )
        manual_link = driver.find_element(By.CSS_SELECTOR, "a[title*='Owners Manual']")
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
        print(f"Error in A.O. Smith primary callback: {e}")
        return None


def aosmith_fallback_callback(driver):
    """
    Callback function for A.O. Smith fallback scraping on hotwater.com after navigating to the product page via DuckDuckGo.
    """
    try:
        # Scroll a bit
        driver.execute_script("window.scrollTo(0,21)")

        # Check if the product is discontinued
        try:
            discontinued_span = driver.find_element(By.XPATH, "//span[contains(text(), 'Series Discontinued')]")
            is_discontinued = True
            print("Product is discontinued, clicking warranty link")
        except:
            is_discontinued = False

        if is_discontinued:
            # For discontinued products, click the literature link text
            WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".support-link--literature > .support-link__text"))
            )
            literature_text = driver.find_element(By.CSS_SELECTOR, ".support-link--literature > .support-link__text")
            literature_text.click()
            time.sleep(1)

            # Then click the Manual link
            WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.LINK_TEXT, "Manual"))
            )
            manual_link = driver.find_element(By.LINK_TEXT, "Manual")
            file_url = manual_link.get_attribute("href")
            title = "A.O. Smith Manual"

            # Click the link, which opens a new window
            manual_link.click()

        else:
            # Normal flow for active products
            # Click the "Product Literature" tab
            WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "tab-C"))
            )
            tab_c = driver.find_element(By.ID, "tab-C")
            ActionChains(driver).move_to_element(tab_c).click().perform()
            time.sleep(2)  # Wait for content to load
            driver.execute_script("window.scrollTo(0,50)")  # Scroll a bit more

            # Find and click a manual link (look for link containing "Manual")
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, "Manual"))
            )
            manual_links = driver.find_elements(By.PARTIAL_LINK_TEXT, "Manual")
            if not manual_links:
                raise Exception("No manual links found")
            manual_link = manual_links[0]  # Click the first one
            file_url = manual_link.get_attribute("href")
            title = manual_link.text or "A.O. Smith Manual"

            # Click the link, which opens a new window
            manual_link.click()

            # Wait for new window and switch
            WebDriverWait(driver, 5).until(lambda d: len(d.window_handles) > 1)
            new_window = [h for h in driver.window_handles if h != driver.current_window_handle][0]
            driver.switch_to.window(new_window)

        return {
            'file_url': file_url,
            'title': title,
            'source_url': driver.current_url,
        }

    except Exception as e:
        print(f"Error in A.O. Smith fallback callback: {e}")
        return None


# Fallback scraping mechanism for A.O. Smith manuals on hotwater.com
def fallback_scrape(model):
    """
    Fallback scraping mechanism for A.O. Smith manuals on hotwater.com.
    """
    # Set download preferences
    temp_dir = create_temp_download_dir()
    download_dir = temp_dir
    options = get_chrome_options(download_dir)

    driver = uc.Chrome(options=options)

    try:
        print(f"Primary scraping failed for {model}, trying fallback on hotwater.com...")
        # Search DuckDuckGo for the model
        safe_driver_get(driver, f"https://duckduckgo.com/?q={model}")
        time.sleep(random.uniform(0.5, 1.0))

        # Wait for search results
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a[data-testid='result-title-a']"))
        )

        # Find the first result link that contains hotwater.com
        result_links = driver.find_elements(By.CSS_SELECTOR, "a[data-testid='result-title-a']")
        trusted_link = None
        for link in result_links:
            href = link.get_attribute('href')
            if href and 'hotwater.com' in href:
                trusted_link = link
                break

        if not trusted_link:
            print("No hotwater.com link found in search results")
            return None

        # Click the trusted link
        trusted_link.click()
        time.sleep(random.uniform(0.5, 1.0))

        # Now on the hotwater.com page, call the callback
        result = aosmith_fallback_callback(driver)

        if result:
            # Wait for download after callback
            pdf_path = wait_for_download(download_dir, timeout=30)

            if pdf_path and validate_pdf_file(pdf_path):
                print(f"Downloaded and validated PDF from fallback: {pdf_path}")
                normalized_model = model.replace('/', '_')
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
                print("No valid PDF downloaded from fallback.")
                return None
        else:
            print("Fallback on hotwater.com failed.")
            return None

    except Exception as e:
        print(f"An error occurred during fallback scraping for model {model}: {e}")
        return None
    finally:
        driver.quit()


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
    # Set download preferences
    temp_dir = create_temp_download_dir()
    download_dir = temp_dir
    options = get_chrome_options(download_dir)

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
            print("Primary DuckDuckGo fallback failed, trying secondary fallback...")
            # Try secondary fallback on hotwater.com
            return fallback_scrape(model)

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