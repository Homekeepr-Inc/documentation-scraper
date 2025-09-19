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
import os
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
from app.config import DEFAULT_BLOB_ROOT

# Import utility functions
sys.path.append(os.path.join(os.path.dirname(__file__)))
from utils import duckduckgo_fallback, validate_pdf_file, wait_for_download, safe_driver_get




def scrape_from_lg_page(driver, model):
    """
    Scrape LG manual from an LG product page (used after DuckDuckGo fallback).

    Args:
        driver: Active Selenium WebDriver instance on an LG page
        model: The model number being scraped

    Returns:
        dict: Scraped data or None if not found
    """
    download_dir = os.path.abspath(DEFAULT_BLOB_ROOT)
    # Clean old PDFs
    for f in os.listdir(download_dir):
        if f.endswith('.pdf'):
            os.remove(os.path.join(download_dir, f))

    try:
        # Perform recorded actions for lg- page
        print("Performing recorded actions for LG page...")
        # Dismiss consent overlay
        driver.execute_script("const consent = document.getElementById('transcend-consent-manager'); if (consent) consent.style.display = 'none';")
        time.sleep(random.uniform(0.03, 0.09))
        # Scroll a bit
        driver.execute_script("window.scrollTo(0,2)")
        time.sleep(random.uniform(0.03, 0.09))

        # Click the manuals tab
        try:
            tab = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "#simple-tab-1 > .MuiTypography-root"))
            )
            tab.click()
            print("Clicked manuals tab.")
            time.sleep(random.uniform(0.03, 0.09))
        except Exception as e:
            print(f"Error clicking manuals tab: {e}")
            return None

        # Get the PDF URL from the button
        try:
            button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".MuiPaper-root:nth-child(1) .MuiGrid-root:nth-child(2) > .MuiTypography-root:nth-child(1)"))
            )
            print(f"Button tag: {button.tag_name}")
            print(f"Button text: {button.text}")
            print(f"Button href: {button.get_attribute('href')}")
            print(f"Button onclick: {button.get_attribute('onclick')}")
            attrs = driver.execute_script("return Array.from(arguments[0].attributes).map(attr => ({name: attr.name, value: attr.value}))", button)
            data_attrs = [attr for attr in attrs if attr['name'].startswith('data')]
            print(f"Button data attributes: {[attr['name'] for attr in data_attrs]}")
            for attr in data_attrs:
                print(f"  {attr['name']}: {attr['value']}")
            pdf_url = button.get_attribute('href')
            if pdf_url:
                print(f"Got PDF URL from href: {pdf_url}")
            else:
                print("No href found, clicking button...")
                button.click()
                print("Clicked PDF download button.")
                # Wait for download
                time.sleep(random.uniform(1.13, 3.02))  # wait for download to complete
                downloads = [f for f in os.listdir(download_dir) if f.endswith('.pdf')]
                if downloads:
                    pdf_url = os.path.join(download_dir, downloads[0])
                    print(f"Downloaded PDF: {pdf_url}")
                else:
                    print("No PDF downloaded")
                    return None
        except Exception as e:
            print(f"Error getting PDF URL: {e}")
            return None

        # Validate PDF
        if pdf_url and (pdf_url.endswith('.pdf') or 'pdf' in pdf_url.lower()):
            title = "Owner's Manual"
            doc_type = 'owner'
            print(f"Found PDF: {title}")
            print(f"URL: {pdf_url}")

            # Download and validate PDF
            try:
                if pdf_url.startswith('/'):
                    # Local file
                    with open(pdf_url, 'rb') as f:
                        content = f.read()
                else:
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
                'brand': 'lg',
                'model_number': model,
                'doc_type': doc_type,
                'title': title,
                'source_url': driver.current_url,
                'file_url': pdf_url,
            }
        else:
            print("No valid PDF URL found after LG page scraping.")
            return None

    except Exception as e:
        print(f"Error scraping from LG page: {e}")
        return None


def scrape_lg_manual(model):
    """
    Scrape the owner's manual PDF for a given LG appliance model.

    Args:
        model (str): The model number (e.g., LMXS28626S)

    Returns:
        dict: Scraped data or None if not found
    """
    url = f"https://www.lg.com/us/support/product/{model}"
    pdf_url = None

    # Launch undetected Chrome
    options = uc.ChromeOptions()
    # options.add_argument('--headless')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-popup-blocking')
    options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    # Set download preferences
    download_dir = os.path.abspath(DEFAULT_BLOB_ROOT)
    os.makedirs(download_dir, exist_ok=True)
    # Clean old PDFs to avoid picking wrong file
    for f in os.listdir(download_dir):
        if f.endswith('.pdf'):
            os.remove(os.path.join(download_dir, f))
    options.add_experimental_option("prefs", {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True
    })

    driver = uc.Chrome(options=options)

    try:
        print(f"Fetching page for model {model}...")
        safe_driver_get(driver, url)
        print(f"Current URL: {driver.current_url}")

        # Wait for JS to render
        time.sleep(random.uniform(0.03, 0.09))

        # Get the page source and parse it
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')

        print(f"Page title: {driver.title}")
        guide_error = soup.find('div', class_='guide-error')
        print(f"Guide error found: {guide_error is not None}")
        page_not_found = 'Page Not Found' in driver.title or "isn't available" in soup.get_text()
        print(f"404 page detected: {page_not_found}")

        # Check for guide-error or 404 and retry with lg- prefix if needed
        if guide_error or page_not_found:
            print(f"Guide error detected for {model}, retrying with lg- prefix...")
            retry_url = f"https://www.lg.com/us/support/product/lg-{model}"
            safe_driver_get(driver, retry_url)
            print(f"Retry URL: {driver.current_url}")
            time.sleep(random.uniform(0.03, 0.09))
            # Dismiss consent overlay
            driver.execute_script("const consent = document.getElementById('transcend-consent-manager'); if (consent) consent.style.display = 'none';")
            time.sleep(random.uniform(0.03, 0.09))
            # Mouse over element to trigger loading
            try:
                element = driver.find_element(By.CSS_SELECTOR, ".MuiBox-root:nth-child(3) .MuiButtonBase-root")
                actions = ActionChains(driver)
                actions.move_to_element(element).perform()
                time.sleep(random.uniform(0.03, 0.09))
            except Exception as e:
                print(f"Mouse over failed: {e}")
            # Scrolling
            driver.execute_script("window.scrollTo(0,5)")
            time.sleep(random.uniform(0.03, 0.09))
            driver.execute_script("window.scrollTo(0,272)")
            time.sleep(random.uniform(0.03, 0.09))
            driver.execute_script("window.scrollTo(0,672)")
            time.sleep(random.uniform(0.03, 0.09))
            url = retry_url  # Update URL for source_url
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            print(f"Retry page title: {driver.title}")
            guide_error_retry = soup.find('div', class_='guide-error')
            print(f"Guide error after retry: {guide_error_retry is not None}")
            # Debug: print first 1000 chars of page source
            print(f"Page source (first 1000 chars): {page_source[:1000]}")



        if 'lg-' in url:
            # New parsing for lg- prefixed pages using recorded actions
            print("Performing recorded actions for lg- page...")
            # Scroll a bit
            driver.execute_script("window.scrollTo(0,2)")
            time.sleep(random.uniform(0.03, 0.09))
            # Click the manuals tab
            try:
                tab = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "#simple-tab-1 > .MuiTypography-root"))
                )
                tab.click()
                print("Clicked manuals tab.")
                time.sleep(random.uniform(0.03, 0.09))
                # Debug: print all manual items
                manuals = driver.find_elements(By.CSS_SELECTOR, ".MuiPaper-root")
                print(f"Found {len(manuals)} manual items:")
                for i, manual in enumerate(manuals):
                    print(f"Manual {i} text: {manual.text}")
            except Exception as e:
                print(f"Error clicking tab: {e}")
                # Fallback to DuckDuckGo search
                return duckduckgo_fallback(driver, model, "lg.com/us", lambda d: scrape_from_lg_page(d, model))
            # Get the PDF URL from the button
            try:
                button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".MuiPaper-root:nth-child(1) .MuiGrid-root:nth-child(2) > .MuiTypography-root:nth-child(1)"))
                )
                print(f"Button tag: {button.tag_name}")
                print(f"Button text: {button.text}")
                print(f"Button href: {button.get_attribute('href')}")
                print(f"Button onclick: {button.get_attribute('onclick')}")
                attrs = driver.execute_script("return Array.from(arguments[0].attributes).map(attr => ({name: attr.name, value: attr.value}))", button)
                data_attrs = [attr for attr in attrs if attr['name'].startswith('data')]
                print(f"Button data attributes: {[attr['name'] for attr in data_attrs]}")
                for attr in data_attrs:
                    print(f"  {attr['name']}: {attr['value']}")
                pdf_url = button.get_attribute('href')
                if pdf_url:
                    print(f"Got PDF URL from href: {pdf_url}")
                else:
                    print("No href found, clicking button...")
                    button.click()
                    print("Clicked PDF download button.")
                    # Wait for download
                    time.sleep(random.uniform(1.13, 3.02))  # wait for download to complete
                    downloads = [f for f in os.listdir(download_dir) if f.endswith('.pdf')]
                    if downloads:
                        pdf_url = os.path.join(download_dir, downloads[0])
                        print(f"Downloaded PDF: {pdf_url}")
                    else:
                        print("No PDF downloaded")
                        return None
            except Exception as e:
                print(f"Error getting PDF URL: {e}")
                return None

            # Validate if it's a PDF URL
            if pdf_url and (pdf_url.endswith('.pdf') or 'pdf' in pdf_url.lower()):
                title = "Owner's Manual"
                doc_type = 'owner'
                print(f"Found PDF: {title}")
                print(f"URL: {pdf_url}")

                # Download and validate PDF
                try:
                    if pdf_url.startswith('/'):
                        # Local file
                        with open(pdf_url, 'rb') as f:
                            content = f.read()
                    else:
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
                    'brand': 'lg',
                    'model_number': model,
                    'doc_type': doc_type,
                    'title': title,
                    'source_url': url,
                    'file_url': pdf_url,
                }
            else:
                print("No valid PDF URL found after click.")
                return None
        else:
            # Original parsing for non-lg pages
            # Check for manualList div
            manual_list = soup.find('div', class_='manualList')
            if not manual_list or not isinstance(manual_list, Tag):
                print("No manual list found on the page.")
                # Debug: find all divs with class containing 'manual'
                import re
                manual_divs = [div for div in soup.find_all('div', class_=re.compile('manual', re.I)) if isinstance(div, Tag)]
                print(f"Divs with 'manual' in class: {[div.get('class') for div in manual_divs]}")
                # Also check for c-resources
                c_resources = soup.find('div', class_=re.compile('c-resources', re.I))
                if c_resources and isinstance(c_resources, Tag):
                    print(f"c-resources div found: True, class: {c_resources.get('class')}")
                else:
                    print("c-resources div found: False")
                print("Page body text (first 500 chars):")
                body = soup.find('body')
                if body:
                    print(body.get_text()[:500])
                else:
                    print("No body found.")
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
    from utils import ingest_manual
    return ingest_manual(result)
def main():
    if len(sys.argv) < 2:
        print("Usage: python3 lg_scraper.py <model_number>")
        sys.exit(1)

    model = sys.argv[1].strip()
    if not model:
        print("Model number cannot be empty.")
        sys.exit(1)

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


if __name__ == "__main__":
    main()