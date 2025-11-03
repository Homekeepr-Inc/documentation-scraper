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
from utils import (
    safe_driver_get,
    wait_for_download,
    validate_pdf_file,
    validate_and_ingest_manual,
    create_temp_download_dir,
    cleanup_temp_dir,
    duckduckgo_fallback,
    get_chrome_options,
    create_chrome_driver,
    homedepot_manual_callback,
)


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

        manual_link_texts = ["Use and Care Manual", "Use and Care Instructions"]

        # Click the first matching "Use and Care ..." link
        manual_link = None
        manual_href = None
        clicked_label = None
        initial_handles = set(driver.window_handles)
        original_url = driver.current_url

        for label in manual_link_texts:
            print(f"Looking for '{label}' link...")
            try:
                WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.LINK_TEXT, label))
                )
                manual_link = driver.find_element(By.LINK_TEXT, label)
                manual_href = manual_link.get_attribute("href")
                driver.execute_script("arguments[0].click();", manual_link)
                print(f"Clicked '{label}' link.")
                clicked_label = label
                break
            except Exception as e:
                print(f"Failed to find or click '{label}' link: {e}")

        if manual_link is None:
            print("No manual link found.")
            return None

        # Wait for manual content to open (new window or navigation)
        target_handle = driver.current_window_handle
        print("Waiting for manual content to open...")
        try:
            WebDriverWait(driver, 5).until(
                lambda d: len(d.window_handles) > len(initial_handles)
            )
            new_handles = [h for h in driver.window_handles if h not in initial_handles]
            if new_handles:
                target_handle = new_handles[0]
        except Exception:
            print("No new window detected; will continue in current window.")

        if target_handle != driver.current_window_handle:
            driver.switch_to.window(target_handle)
            time.sleep(0.2)
            print("Switched to new window.")
        else:
            try:
                WebDriverWait(driver, 5).until(lambda d: d.current_url != original_url)
            except Exception:
                print("Manual content did not trigger navigation; continuing anyway.")
            print("Continuing in current window for manual download.")

        # On the manual page, click the first matching link to trigger download (if needed)
        download_link = None
        file_url = None
        title = None
        for label in manual_link_texts:
            print(f"Looking for second '{label}' link...")
            try:
                WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.LINK_TEXT, label))
                )
                download_link = driver.find_element(By.LINK_TEXT, label)
                file_url = download_link.get_attribute("href")
                title = download_link.text or label
                driver.execute_script("arguments[0].click();", download_link)
                time.sleep(0.2)
                print(f"Clicked second '{label}' link, download triggered.")
                break
            except Exception as e:
                print(f"No second '{label}' link found or clickable: {e}")

        if not file_url:
            file_url = driver.current_url if driver.current_url != 'about:blank' else manual_href

        if not title:
            title = clicked_label or "Rheem Use and Care Manual"

        if download_link is None:
            print("No secondary manual link found; assuming current page is the PDF.")
            file_url = file_url or manual_href

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
    """Reuse the generic Home Depot fallback with Rheem-specific defaults."""

    return homedepot_manual_callback(
        driver,
        model,
        manual_link_texts=["Use and Care Manual"],
        expand_headers=["Product Details"],
    )




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
        model (str): The model number (e.g., XG40T06EN38U0)

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
        print("Attempting primary on rheem.com with progressive model trimming...")
        primary_host = 'rheem.com'
        result = duckduckgo_fallback(
            driver,
            model,
            primary_host,
            lambda d: rheem_rheem_callback(d, model),
            '\"{model}\" site:rheem.com',
            max_model_trim=5,
            allowed_hosts=("www.rheem.com", "rheem.com"),
        )

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
            result = duckduckgo_fallback(
                driver,
                model,
                fallback_url,
                lambda d: rheem_homedepot_callback(d, model),
                f"{model} site:{fallback_url}",
                allowed_hosts=("www.homedepot.com", "homedepot.com"),
            )

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
            result = duckduckgo_fallback(driver, model, supplyhouse_url, lambda d: rheem_supplyhouse_callback(d, model), f"{model} site:{supplyhouse_url}")

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
