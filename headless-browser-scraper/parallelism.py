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

parallelism_count = 2
# Global queue for all scraper jobs
job_queue = queue.Queue()

# Semaphore to limit to 2 concurrent browsers
browser_semaphore = threading.Semaphore(parallelism_count)

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

        browser_semaphore.acquire()  # Limit to 2 concurrent browsers
        try:
            print(f"Starting scrape for {brand} {model} (job {job_id})")

            # Import the appropriate scraper function
            if brand == 'lg':
                from lg_scraper import scrape_lg_manual
                result = scrape_lg_manual(model)
            elif brand == 'ge':
                from ge_headless_scraper import scrape_ge_manual
                result = scrape_ge_manual(model)
            elif brand == 'whirlpool':
                from whirlpool_headless_scraper import scrape_whirlpool_manual
                result = scrape_whirlpool_manual(model)
            elif brand == 'kitchenaid':
                from kitchenaid_headless_scraper import scrape_kitchenaid_manual
                result = scrape_kitchenaid_manual(model)
            elif brand == 'samsung':
                from samsung_headless_scraper import scrape_samsung_manual
                result = scrape_samsung_manual(model)
            elif brand == 'frigidaire':
                from frigidaire.frigidaire_headless_scraper import scrape_frigidaire_manual
                result = scrape_frigidaire_manual(model)
            else:
                result = None  # Unknown brand

            set_job_result(job_id, result)
            print(f"Completed scrape for {brand} {model} (job {job_id})")

        except Exception as e:
            print(f"Error in worker for job {job_id}: {e}")
            set_job_result(job_id, e)
        finally:
            browser_semaphore.release()
        job_queue.task_done()


# Start 2 worker threads
worker_threads = []
for i in range(parallelism_count):
    t = threading.Thread(target=worker, daemon=True)
    t.start()
    worker_threads.append(t)