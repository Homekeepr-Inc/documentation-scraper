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
from selenium.common.exceptions import ElementClickInterceptedException
from bs4 import BeautifulSoup, Tag
import requests

# Add paths to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))  # project root
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))  # headless-browser-scraper

# Import utility functions
from utils import safe_driver_get, wait_for_download, validate_pdf_file, validate_and_ingest_manual, create_temp_download_dir, cleanup_temp_dir, duckduckgo_fallback, get_chrome_options


def rheem_rheem_callback(driver, model):
    """
    Callback function for Rheem scraping on rheem.com after navigating to the product page via DuckDuckGo.
    """
    try:
        # Check if the model number is present on the page
        if model.lower() not in driver.page_source.lower():
            print(f"Model {model} not found on the page.")
            return None

        # Scroll down
        driver.execute_script("window.scrollTo(0,142)")
        time.sleep(0.5)
        driver.execute_script("window.scrollTo(0,592)")
        time.sleep(0.5)

        # Click the "Documentation" accordion button
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[text()='Documentation']"))
        )
        accordion_button = driver.find_element(By.XPATH, "//button[text()='Documentation']")
        driver.execute_script("arguments[0].scrollIntoView();", accordion_button)
        time.sleep(0.5)
        driver.execute_script("arguments[0].click();", accordion_button)
        time.sleep(1)

        # Click "Use and Care Instructions" link
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Use and Care Instructions"))
        )
        manual_link = driver.find_element(By.LINK_TEXT, "Use and Care Instructions")
        manual_link.click()

        # Wait for new window and switch
        WebDriverWait(driver, 10).until(lambda d: len(d.window_handles) > 1)
        new_window = [h for h in driver.window_handles if h != driver.current_window_handle][0]
        driver.switch_to.window(new_window)
        time.sleep(1)

        # On the new page, click "Use and Care Instructions" again to trigger download
        try:
            WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.LINK_TEXT, "Use and Care Instructions"))
            )
            download_link = driver.find_element(By.LINK_TEXT, "Use and Care Instructions")
            file_url = download_link.get_attribute("href")
            title = download_link.text or "Rheem Use and Care Instructions"
            download_link.click()
            time.sleep(2)
        except:
            # If no second link, perhaps the first click opened the PDF
            file_url = driver.current_url
            title = "Rheem Use and Care Instructions"

        source_url = driver.current_url if driver.current_url != 'about:blank' else file_url

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
        # Check if the model number is present on the page
        if model.lower() not in driver.page_source.lower():
            print(f"Model {model} not found on the page.")
            return None

        # Scroll down to load content
        driver.execute_script("window.scrollTo(0,1460)")
        time.sleep(1)
        driver.execute_script("window.scrollTo(0,2151)")
        time.sleep(1)

        # Click "Product Details" to expand
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//h3[text()='Product Details']"))
        )
        product_details = driver.find_element(By.XPATH, "//h3[text()='Product Details']")
        product_details.click()
        time.sleep(1)

        # Find the "Use and Care Manual" link
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Use and Care Manual"))
        )
        manual_link = driver.find_element(By.LINK_TEXT, "Use and Care Manual")

        file_url = manual_link.get_attribute("href")
        title = manual_link.text or "Rheem Use and Care Manual"
        
        try:
            print(f"Clicking manual link: {manual_link.text}")
            manual_link.click()
        except ElementClickInterceptedException:
            print("Click intercepted, navigating to href directly.")
            safe_driver_get(driver, file_url)

        time.sleep(5)  # Wait for download or new window

        # Check if new window opened
        if len(driver.window_handles) > 1:
            new_window = [h for h in driver.window_handles if h != driver.current_window_handle][0]
            driver.switch_to.window(new_window)
            source_url = driver.current_url if driver.current_url != 'about:blank' else file_url
        else:
            source_url = file_url

        return {
            'file_url': file_url,
            'title': title,
            'source_url': source_url,
        }

    except Exception as e:
        print(f"Error in Rheem callback: {e}")
        return None




def rheem_supplyhouse_callback(driver, model):
    """
    Callback function for Rheem scraping on supplyhouse.com after navigating to the product page via DuckDuckGo.
    """
    try:
        # Check if the model number is present on the page
        if model.lower() not in driver.page_source.lower():
            print(f"Model {model} not found on the page.")
            return None

        # Scroll down to load content
        driver.execute_script("window.scrollTo(0, 500)")
        time.sleep(0.5)

        # Mouse over the first element
        element = driver.find_element(By.CSS_SELECTOR, ".kNBVuQ > .Box-sc-1z9git-0:nth-child(1) .dBGvTK")
        actions = ActionChains(driver)
        actions.move_to_element(element).perform()
        time.sleep(0.5)

        # Click the second element to open the manual
        element2 = driver.find_element(By.CSS_SELECTOR, ".kNBVuQ > .Box-sc-1z9git-0:nth-child(2) .dBGvTK")
        actions.move_to_element(element2).perform()
        element2.click()

        # Wait for new window and switch
        WebDriverWait(driver, 10).until(lambda d: len(d.window_handles) > 1)
        new_window = [h for h in driver.window_handles if h != driver.current_window_handle][0]
        driver.switch_to.window(new_window)
        time.sleep(1)

        # Assume the PDF is now loaded in the new window
        file_url = driver.current_url
        title = "Rheem User Manual"
        source_url = file_url

        return {
            'file_url': file_url,
            'title': title,
            'source_url': source_url,
        }

    except Exception as e:
        print(f"Error in Rheem supplyhouse callback: {e}")
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

    driver = uc.Chrome(options=options)

    try:
        print(f"Attempting DuckDuckGo fallback for Rheem model {model}...")

        # Use rheem.com as primary
        primary_url = 'rheem.com/products'
        result = duckduckgo_fallback(driver, model, primary_url, lambda d: rheem_rheem_callback(d, model), f"\"{model}\" site:{primary_url}")

        if result:
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
            # Wait for download after callback
            pdf_path = wait_for_download(download_dir, timeout=30)

            if pdf_path and validate_pdf_file(pdf_path):
                print(f"Downloaded and validated PDF from fallback: {pdf_path}")
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
                print("No valid PDF downloaded from fallback.")
                result = None

        if not result:
            print("Fallback on homedepot.com failed, trying supplyhouse.com...")
            supplyhouse_url = 'supplyhouse.com'
            result = duckduckgo_fallback(driver, model, supplyhouse_url, lambda d: rheem_supplyhouse_callback(d, model), f"{model} owner's manual site:{supplyhouse_url}")

        if result:
            # Wait for download after callback
            pdf_path = wait_for_download(download_dir, timeout=30)

            if pdf_path and validate_pdf_file(pdf_path):
                print(f"Downloaded and validated PDF from supplyhouse: {pdf_path}")
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
                print("No valid PDF downloaded from supplyhouse.")
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