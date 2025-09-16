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
from selenium.webdriver.common.action_chains import ActionChains
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
    url = f"https://www.lg.com/us/support/product/{model}"

    # Launch undetected Chrome (non-headless for debugging)
    options = uc.ChromeOptions()
    # options.add_argument('--headless')  # Disabled for debugging
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-popup-blocking')
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

        print(f"Page title: {driver.title}")
        guide_error = soup.find('div', class_='guide-error')
        print(f"Guide error found: {guide_error is not None}")
        page_not_found = 'Page Not Found' in driver.title or "isn't available" in soup.get_text()
        print(f"404 page detected: {page_not_found}")

        # Check for guide-error or 404 and retry with lg- prefix if needed
        if guide_error or page_not_found:
            print(f"Guide error detected for {model}, retrying with lg- prefix...")
            retry_url = f"https://www.lg.com/us/support/product/lg-{model}"
            driver.get(retry_url)
            print(f"Retry URL: {driver.current_url}")
            time.sleep(5)
            # Dismiss consent overlay
            driver.execute_script("const consent = document.getElementById('transcend-consent-manager'); if (consent) consent.style.display = 'none';")
            time.sleep(2)
            # Mouse over element to trigger loading
            try:
                element = driver.find_element(By.CSS_SELECTOR, ".MuiBox-root:nth-child(3) .MuiButtonBase-root")
                actions = ActionChains(driver)
                actions.move_to_element(element).perform()
                time.sleep(1)
            except Exception as e:
                print(f"Mouse over failed: {e}")
            # Scrolling
            driver.execute_script("window.scrollTo(0,5)")
            time.sleep(1)
            driver.execute_script("window.scrollTo(0,272)")
            time.sleep(1)
            driver.execute_script("window.scrollTo(0,672)")
            time.sleep(1)
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            url = retry_url  # Update URL for source_url
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
            time.sleep(2)
            # Click the manuals tab
            try:
                tab = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "#simple-tab-1 > .MuiTypography-root"))
                )
                tab.click()
                print("Clicked manuals tab.")
                time.sleep(2)
            except Exception as e:
                print(f"Error clicking tab: {e}")
                return None
            # Get the PDF URL from the button
            try:
                button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, ".MuiPaper-root:nth-child(1) .MuiGrid-root:nth-child(2) > .MuiTypography-root:nth-child(1)"))
                )
                pdf_url = button.get_attribute('href')
                if pdf_url:
                    print(f"Got PDF URL from href: {pdf_url}")
                else:
                    print("No href found, clicking button...")
                    original_handles = driver.window_handles
                    button.click()
                    print("Clicked PDF download button.")
                    # Wait for new window
                    try:
                        WebDriverWait(driver, 10).until(
                            lambda d: len(d.window_handles) > len(original_handles)
                        )
                        print("New window opened.")
                    except Exception as e:
                        print(f"Timeout waiting for new window: {e}")
                        return None
                    # Switch to new window
                    new_handle = [h for h in driver.window_handles if h not in original_handles][0]
                    driver.switch_to.window(new_handle)
                    # Wait for URL to load
                    try:
                        WebDriverWait(driver, 10).until(lambda d: d.current_url != "about:blank")
                    except:
                        print("URL remained about:blank")
                    pdf_url = driver.current_url
                    print(f"Switched to new window, URL: {pdf_url}")
                    # Close new window and switch back
                    driver.close()
                    driver.switch_to.window(original_handles[0])
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