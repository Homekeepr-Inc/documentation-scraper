#!/usr/bin/env python3
"""
Rheem Appliance Manuals Headless Scraper

Uses undetected-chromedriver for stealthy headless scraping to avoid bot detection.
Extracts owner's manual PDFs from homedepot.com.
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
from utils import safe_driver_get, wait_for_download, validate_pdf_file, validate_and_ingest_manual, create_temp_download_dir, cleanup_temp_dir, duckduckgo_fallback, get_chrome_options, create_chrome_driver


def rheem_rheem_callback(driver, model):
    """
    Callback function for Rheem scraping on rheem.com after navigating to the product page via DuckDuckGo.
    """
    try:
        print(f"Starting Rheem rheem.com callback for model {model}")
        print(f"Current URL: {driver.current_url}")

        # Check if the model number is present on the page
        if model.lower() not in driver.page_source.lower():
            print(f"Model {model} not found in page source.")
            return None
        print(f"Model {model} found in page source.")

        # Scroll down
        print("Scrolling to documentation section...")
        driver.execute_script("window.scrollTo(0,142)")
        time.sleep(0.2)
        driver.execute_script("window.scrollTo(0,592)")
        time.sleep(0.2)
        print("Scrolled.")

        # Click the "Documentation" accordion button
        print("Looking for 'Documentation' button...")
        try:
            WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[text()='Documentation']"))
            )
            accordion_button = driver.find_element(By.XPATH, "//button[text()='Documentation']")
            driver.execute_script("arguments[0].scrollIntoView();", accordion_button)
            time.sleep(0.2)
            driver.execute_script("arguments[0].click();", accordion_button)
            time.sleep(0.2)
            print("'Documentation' accordion expanded.")
        except Exception as e:
            print(f"Failed to find or click 'Documentation' button: {e}")
            return None

        # Click "Use and Care Manual" link
        print("Looking for 'Use and Care Manual' link...")
        try:
            WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.LINK_TEXT, "Use and Care Manual"))
            )
            manual_link = driver.find_element(By.LINK_TEXT, "Use and Care Manual")
            manual_link.click()
            print("Clicked 'Use and Care Manual' link.")
        except Exception as e:
            print(f"Failed to find or click 'Use and Care Manual' link: {e}")
            return None

        # Wait for new window and switch
        print("Waiting for new window...")
        try:
            WebDriverWait(driver, 5).until(lambda d: len(d.window_handles) > 1)
            new_window = [h for h in driver.window_handles if h != driver.current_window_handle][0]
            driver.switch_to.window(new_window)
            time.sleep(0.2)
            print("Switched to new window.")
        except Exception as e:
            print(f"Failed to wait for or switch to new window: {e}")
            return None

        # On the new page, click "Use and Care Manual" again to trigger download
        print("Looking for second 'Use and Care Manual' link...")
        try:
            WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.LINK_TEXT, "Use and Care Manual"))
            )
            download_link = driver.find_element(By.LINK_TEXT, "Use and Care Manual")
            file_url = download_link.get_attribute("href")
            title = download_link.text or "Rheem Use and Care Manual"
            download_link.click()
            time.sleep(0.2)
            print("Clicked second link, download triggered.")
        except Exception as e:
            print(f"No second link found, assuming PDF opened directly: {e}")
            # If no second link, perhaps the first click opened the PDF
            file_url = driver.current_url
            title = "Rheem Use and Care Manual"

        source_url = driver.current_url if driver.current_url != 'about:blank' else file_url
        print(f"Extracted file_url: {file_url}, title: {title}, source_url: {source_url}")

        print("Callback successful.")
        return {
            'file_url': file_url,
            'title': title,
            'source_url': source_url,
        }

    except Exception as e:
        print(f"Error in Rheem rheem.com callback: {e}")
        return None


def rheem_homedepot_callback(driver, model):
    """
    Callback function for Rheem scraping on homedepot.com after navigating to the product page via DuckDuckGo.
    """
    try:
        print(f"Starting Rheem Home Depot callback for model {model}")
        print(f"Current URL: {driver.current_url}")

        # Wait for page to load
        print("Waiting for page body to load...")
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.TAG_NAME, 'body'))
        )
        print("Page body loaded.")

        # Check if the model number is present on the page
        if model.lower() not in driver.page_source.lower():
            print(f"Model {model} not found in page source.")
            return None
        print(f"Model {model} found in page source.")

        # Scroll down to load content
        print("Scrolling to load content...")
        driver.execute_script("window.scrollTo(0,500)")
        time.sleep(0.2)
        driver.execute_script("window.scrollTo(0,1000)")
        time.sleep(0.2)
        print("Scrolled to content area.")

        # Click "Product Details" to expand
        print("Looking for 'Product Details' h3...")
        try:
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//h3[contains(text(), 'Product Details')]"))
            )
            product_details = driver.find_element(By.XPATH, "//h3[contains(text(), 'Product Details')]")
            print("Found 'Product Details', scrolling into view...")
            driver.execute_script("arguments[0].scrollIntoView();", product_details)
            time.sleep(0.2)
            print("Clicking 'Product Details' with JS...")
            driver.execute_script("arguments[0].click();", product_details)
            print("Clicked 'Product Details', waiting for content to load...")
            time.sleep(0.2)
        except Exception as e:
            print(f"Failed to find or click 'Product Details': {e}")
            return None

        # Find the "Use and Care Manual" link
        print("Looking for 'Use and Care Manual' link...")
        try:
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.LINK_TEXT, "Use and Care Manual"))
            )
            manual_link = driver.find_element(By.LINK_TEXT, "Use and Care Manual")
            print("Found 'Use and Care Manual' link.")
        except Exception as e:
            print(f"Failed to find 'Use and Care Manual' link: {e}")
            # Fallback to XPath
            try:
                manual_link = driver.find_element(By.XPATH, "//a[contains(text(), 'Use and Care Manual')]")
                print("Found link using XPath fallback.")
            except Exception as e2:
                print(f"XPath fallback also failed: {e2}")
                return None

        file_url = manual_link.get_attribute("href")
        title = manual_link.text or "Rheem Use and Care Manual"
        print(f"Extracted file_url: {file_url}, title: {title}")

        print(f"Navigating to manual link: {title}")
        safe_driver_get(driver, file_url)

        time.sleep(0.2)
        print("Waited 5 seconds after navigation.")

        # Check if new window opened
        if len(driver.window_handles) > 1:
            print("New window detected, switching...")
            new_window = [h for h in driver.window_handles if h != driver.current_window_handle][0]
            driver.switch_to.window(new_window)
            source_url = driver.current_url if driver.current_url != 'about:blank' else file_url
            print(f"Switched to new window, source_url: {source_url}")
        else:
            source_url = file_url
            print("No new window, using file_url as source_url.")

        print("Callback successful.")
        return {
            'file_url': file_url,
            'title': title,
            'source_url': source_url,
        }

    except Exception as e:
        print(f"Error in Rheem Home Depot callback: {e}")
        return None




def rheem_supplyhouse_callback(driver, model):
    """
    Callback function for Rheem scraping on supplyhouse.com after navigating to the product page via DuckDuckGo.
    """
    try:
        print(f"Starting Rheem SupplyHouse callback for model {model}")
        print(f"Current URL: {driver.current_url}")

        # Check if the model number is present on the page
        if model.lower() not in driver.page_source.lower():
            print(f"Model {model} not found in page source.")
            return None
        print(f"Model {model} found in page source.")

        # Scroll down to load content
        print("Scrolling to load content...")
        driver.execute_script("window.scrollTo(0, 500)")
        time.sleep(0.2)
        print("Scrolled.")

        # Mouse over the first element
        print("Looking for first element to hover...")
        try:
            element = driver.find_element(By.CSS_SELECTOR, ".kNBVuQ > .Box-sc-1z9git-0:nth-child(1) .dBGvTK")
            actions = ActionChains(driver)
            actions.move_to_element(element).perform()
            time.sleep(0.2)
            print("Hovered over first element.")
        except Exception as e:
            print(f"Failed to find or hover first element: {e}")
            return None

        # Click the second element to open the manual
        print("Looking for second element to click...")
        try:
            element2 = driver.find_element(By.CSS_SELECTOR, ".kNBVuQ > .Box-sc-1z9git-0:nth-child(2) .dBGvTK")
            actions.move_to_element(element2).perform()
            element2.click()
            print("Clicked second element.")
        except Exception as e:
            print(f"Failed to find or click second element: {e}")
            return None

        # Wait for new window and switch
        print("Waiting for new window...")
        try:
            WebDriverWait(driver, 5).until(lambda d: len(d.window_handles) > 1)
            new_window = [h for h in driver.window_handles if h != driver.current_window_handle][0]
            driver.switch_to.window(new_window)
            time.sleep(0.2)
            print("Switched to new window.")
        except Exception as e:
            print(f"Failed to wait for or switch to new window: {e}")
            return None

        # Assume the PDF is now loaded in the new window
        file_url = driver.current_url
        title = "Rheem User Manual"
        source_url = file_url
        print(f"Extracted file_url: {file_url}, title: {title}")

        print("Callback successful.")
        return {
            'file_url': file_url,
            'title': title,
            'source_url': source_url,
        }

    except Exception as e:
        print(f"Error in Rheem SupplyHouse callback: {e}")
        return None


def scrape_rheem_manual(model):
    """
    Scrape the owner's manual PDF for a given Rheem appliance model using DuckDuckGo fallback.

    Args:
        model (str): The model number (e.g., XG40T06EN38U1)

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

    driver = create_chrome_driver(options=options)

    try:
        print(f"Starting scrape for Rheem model {model}...")

        # Use rheem.com as primary
        print("Attempting primary on rheem.com...")
        primary_url = 'rheem.com/products'
        result = duckduckgo_fallback(driver, model, primary_url, lambda d: rheem_rheem_callback(d, model), f"\"{model}\" site:{primary_url}")

        if result:
            print("Primary callback returned result, waiting for download...")
            # Wait for download after callback
            pdf_path = wait_for_download(download_dir, timeout=30)

            if pdf_path and validate_pdf_file(pdf_path):
                print(f"Downloaded and validated PDF from primary: {pdf_path}")
                return {
                    'brand': 'rheem',
                    'model_number': normalized_model,
                    'doc_type': 'owner',
                    'title': result['title'],
                    'source_url': result['source_url'],
                    'file_url': result['file_url'],
                    'local_path': pdf_path,
                }
            else:
                print("No valid PDF downloaded from primary.")
                result = None

        if not result:
            print("Primary on rheem.com failed, trying fallback on homedepot.com...")
            # Fallback to homedepot.com
            fallback_url = 'homedepot.com'
            result = duckduckgo_fallback(driver, model, fallback_url, lambda d: rheem_homedepot_callback(d, model), f"{model} owner's manual site:{fallback_url}")

        if result:
            print("Home Depot callback returned result, waiting for download...")
            # Wait for download after callback
            pdf_path = wait_for_download(download_dir, timeout=30)

            if pdf_path and validate_pdf_file(pdf_path):
                print(f"Downloaded and validated PDF from Home Depot: {pdf_path}")
                return {
                    'brand': 'rheem',
                    'model_number': normalized_model,
                    'doc_type': 'owner',
                    'title': result['title'],
                    'source_url': result['source_url'],
                    'file_url': result['file_url'],
                    'local_path': pdf_path,
                }
            else:
                print("No valid PDF downloaded from Home Depot.")
                result = None

        if not result:
            print("Fallback on homedepot.com failed, trying supplyhouse.com...")
            supplyhouse_url = 'supplyhouse.com'
            result = duckduckgo_fallback(driver, model, supplyhouse_url, lambda d: rheem_supplyhouse_callback(d, model), f"{model} owner's manual site:{supplyhouse_url}")

        if result:
            print("SupplyHouse callback returned result, waiting for download...")
            # Wait for download after callback
            pdf_path = wait_for_download(download_dir, timeout=30)

            if pdf_path and validate_pdf_file(pdf_path):
                print(f"Downloaded and validated PDF from SupplyHouse: {pdf_path}")
                return {
                    'brand': 'rheem',
                    'model_number': normalized_model,
                    'doc_type': 'owner',
                    'title': result['title'],
                    'source_url': result['source_url'],
                    'file_url': result['file_url'],
                    'local_path': pdf_path,
                }
            else:
                print("No valid PDF downloaded from SupplyHouse.")
                return None
        else:
            print("Fallback on supplyhouse.com failed.")
            return None

    except Exception as e:
        print(f"An error occurred during scraping for Rheem {model}: {e}")
        return None

    finally:
        driver.quit()


def ingest_rheem_manual(result):
    from utils import validate_and_ingest_manual
    # Rheem PDFs may not contain exact model numbers, so disable content validation
    return validate_and_ingest_manual(result, False)


def main():
    if len(sys.argv) != 2:
        print("Usage: python3 rheem_headless_scraper.py <model_number>")
        sys.exit(1)

    model = sys.argv[1].strip()
    if not model:
        print("Model number cannot be empty.")
        sys.exit(1)

    results = scrape_rheem_manual(model)
    if results:
        print("Scraping successful!")
        print(results)
        # Optionally ingest
        ingest_result = ingest_rheem_manual(results)
        if ingest_result:
            print(f"Ingested with ID: {ingest_result.id}")
    else:
        print("Scraping failed.")


if __name__ == "__main__":
    main()