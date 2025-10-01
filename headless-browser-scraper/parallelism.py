#!/usr/bin/env python3
"""
Global parallelism control for headless scrapers.

This module provides a shared queue and semaphore to limit concurrent browser instances
across all scrapers to prevent resource exhaustion.
"""

import queue
import threading
import uuid
from typing import Dict, Any, Optional

# Import utils for driver creation and reset
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__)))
from utils import create_chrome_driver, reset_driver

parallelism_count = 4
# Global queue for all scraper jobs
job_queue = queue.Queue()

# Semaphore to limit to parallelism_count concurrent browsers
browser_semaphore = threading.Semaphore(parallelism_count)

# Driver pool: queue of available drivers
driver_pool = queue.Queue(maxsize=parallelism_count)

# Dict to store job results: job_id -> result
job_results: Dict[str, Any] = {}

# Lock for results dict
results_lock = threading.Lock()


def enqueue_scrape_job(brand: str, model: str) -> str:
    """
    Enqueue a scraping job for the given brand and model.

    Args:
        brand (str): The brand (e.g., 'lg', 'ge', 'whirlpool', 'kitchenaid')
        model (str): The model number

    Returns:
        str: Unique job ID
    """
    job_id = str(uuid.uuid4())
    job = {
        'job_id': job_id,
        'brand': brand.lower(),
        'model': model
    }
    job_queue.put(job)
    return job_id


def get_job_result(job_id: str) -> Optional[Any]:
    """
    Get the result of a completed job.

    Args:
        job_id (str): The job ID

    Returns:
        Any: The result if completed, None if still pending
    """
    with results_lock:
        return job_results.get(job_id)


def is_job_complete(job_id: str) -> bool:
    """Check if a job has completed."""
    with results_lock:
        return job_id in job_results


def set_job_result(job_id: str, result: Any):
    """
    Set the result for a completed job.

    Args:
        job_id (str): The job ID
        result (Any): The result to store
    """
    with results_lock:
        job_results[job_id] = result


def worker():
    """Worker thread to process jobs from the global queue."""
    while True:
        try:
            job = job_queue.get(timeout=1)  # Wait for a job
        except queue.Empty:
            continue  # Keep waiting

        job_id = job['job_id']
        brand = job['brand']
        model = job['model']

        # Get a driver from the pool, create if none available
        try:
            driver = driver_pool.get(timeout=0.1)
        except queue.Empty:
            driver = create_chrome_driver()
        try:
            print(f"Starting scrape for {brand} {model} (job {job_id})")

            # Reset driver state
            reset_driver(driver)

            # Create temp download dir for this job
            from utils import create_temp_download_dir
            temp_dir = create_temp_download_dir()

            # Set download path for this job
            driver.execute_cdp_cmd("Page.setDownloadBehavior", {
                "behavior": "allow",
                "downloadPath": temp_dir
            })

            # Import the appropriate scraper function and call with driver and temp_dir
            if brand == 'lg':
                from lg_scraper import scrape_lg_manual
                result = scrape_lg_manual(model, driver, temp_dir)
            elif brand == 'ge':
                from ge.ge_headless_scraper import scrape_ge_manual
                result = scrape_ge_manual(model, driver, temp_dir)
            elif brand == 'whirlpool':
                from whirlpool.whirlpool_headless_scraper import scrape_whirlpool_manual
                result = scrape_whirlpool_manual(model, driver, temp_dir)
            elif brand == 'kitchenaid':
                from kitchenaid.kitchenaid_headless_scraper import scrape_kitchenaid_manual
                result = scrape_kitchenaid_manual(model, driver, temp_dir)
            elif brand == 'samsung':
                from samsung.samsung_headless_scraper import scrape_samsung_manual
                result = scrape_samsung_manual(model, driver, temp_dir)
            elif brand == 'frigidaire':
                from frigidaire.frigidaire_headless_scraper import scrape_frigidaire_manual
                result = scrape_frigidaire_manual(model, driver, temp_dir)
            elif brand == 'aosmith':
                from aosmith.aosmith_headless_scraper import scrape_aosmith_manual
                result = scrape_aosmith_manual(model, driver, temp_dir)
            elif brand == 'rheem':
                from rheem.rheem_headless_scraper import scrape_rheem_manual
                result = scrape_rheem_manual(model, driver, temp_dir)
            else:
                result = None  # Unknown brand

            set_job_result(job_id, result)
            print(f"Completed scrape for {brand} {model} (job {job_id})")

        except Exception as e:
            print(f"Error in worker for job {job_id}: {e}")
            set_job_result(job_id, e)
        finally:
            # Return driver to pool
            driver_pool.put(driver)
        job_queue.task_done()


# Start parallelism_count worker threads
worker_threads = []
for i in range(parallelism_count):
    t = threading.Thread(target=worker, daemon=True)
    t.start()
    worker_threads.append(t)

# Initialize driver pool (lazy creation to avoid startup issues)
# Drivers will be created on first use in worker