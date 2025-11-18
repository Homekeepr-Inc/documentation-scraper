# Replacement of AI Captcha Solver with 2Captcha
**Date:** Tue Nov 18 2025

## Why this is necessary
Maintaining the current custom AI captcha solver has shown to be very time consuming, namely due to the performance differences between local dev machines and the Hetzner VPS. The headless mode is difficult to test compared to launching a regular browser, and debugging inconsistencies in performance has shown to also be very time consuming. We can deprecate our homemade captcha solver and switch to a faster, cheaper, and more reliable service.

## 1. Analysis of Current Implementation
*   **Entry Point:** `serpapi_scraper/orchestrator.py` uses `serpapi_scraper/manualslib_scraper.py` to download manuals.
*   **Captcha Handling:** `manualslib_scraper.py` imports `detect_recaptcha` and `solve_recaptcha_if_present` from `serpapi_scraper/ai_captcha_bridge.py`.
*   **Current Solver:** `ai_captcha_bridge.py` currently loads and uses `serpapi_scraper/ai-captcha-bypass/main.py` to visually solve the captcha using Selenium and AI models (OpenAI/Gemini).
*   **Integration Point:** The best place to swap the implementation is `serpapi_scraper/ai_captcha_bridge.py`. This preserves the interface used by `manualslib_scraper.py` (`detect_recaptcha`, `solve_recaptcha_if_present`) while changing the underlying solving mechanism.

## 2. Proposed Changes

### A. Modify `serpapi_scraper/ai_captcha_bridge.py`
We will completely rewrite the implementation of `solve_recaptcha_if_present` to use the 2Captcha API instead of the local AI solver.

1.  **Remove Dependencies:**
    *   Remove imports and logic related to `ai-captcha-bypass` and dynamic module loading.
    *   Remove Selenium interactions that click tiles or checkboxes (2Captcha solves it server-side).

2.  **Implement 2Captcha Logic:**
    *   **Sitekey Extraction:** Implement a helper to extract the `data-sitekey` from the `div.g-recaptcha` element or the `k` parameter from the reCAPTCHA iframe `src`.
    *   **API Submission:** Send the `sitekey` and the current page URL (`driver.current_url`) to 2Captcha's `in.php` endpoint.
    *   **Polling:** Poll 2Captcha's `res.php` endpoint until a solution token is received.
        *   **Initial Delay:** Wait 15-20 seconds before the first poll request to allow the worker time to solve.
        *   **Polling Interval:** Poll every 5 seconds thereafter.
        *   **Timeout:** Implement a strict timeout (e.g., 120 seconds) to prevent infinite loops if the service is slow.
    *   **Error Handling:** Handle specific API responses:
        *   `CAPCHA_NOT_READY`: Continue polling.
        *   `ERROR_ZERO_BALANCE`, `ERROR_WRONG_USER_KEY`: Log error and fail fast.
    *   **Token Injection:** Once the token is received, use `driver.execute_script` to inject it into the hidden `g-recaptcha-response` textarea.
        *   **Selector:** Use `[name="g-recaptcha-response"]` to ensure compatibility with the scraper's logic (which specifically looks for this name).
        *   **Visibility:** Optionally make the element visible (`display: block`) for debugging, though strictly setting the `.value` is sufficient for the scraper's AJAX hook.

3.  **Environment Configuration:**
    *   The implementation will require a `TWO_CAPTCHA_API_KEY` environment variable.

### B. Verification
*   The `manualslib_scraper.py` logic relies on reading the value of `[name="g-recaptcha-response"]` to construct its AJAX payload. By injecting the 2Captcha token into this element, the existing scraper logic will work without modification.

## 3. Step-by-Step Implementation Plan

1.  **Update `serpapi_scraper/ai_captcha_bridge.py`**:
    *   Import `requests` and `time`.
    *   Define `TWO_CAPTCHA_API_KEY` from `os.getenv`.
    *   Create `solve_recaptcha_v2(driver)` function that:
        *   Finds the sitekey.
        *   Submits the job to 2Captcha.
        *   Waits for the result (with backoff and timeout).
        *   Injects the result into the DOM.
    *   Update `solve_recaptcha_if_present` to call this new function.

2.  **Testing**:
    *   Verify that `manualslib_scraper.py` successfully downloads manuals when a captcha is presented.

## 4. Code Snippet for `ai_captcha_bridge.py` (Preview)

```python
import time
import requests
import os

def solve_recaptcha_if_present(driver: WebDriver, ...) -> bool:
    # 1. Extract Sitekey
    try:
        # Try finding the container first
        element = driver.find_element(By.CLASS_NAME, "g-recaptcha")
        site_key = element.get_attribute("data-sitekey")
        
        # Fallback: Extract from iframe src
        if not site_key:
            iframe = driver.find_element(By.XPATH, "//iframe[contains(@src, 'recaptcha')]")
            src = iframe.get_attribute("src")
            # ... parse 'k' parameter from src ...
    except Exception:
        return False # No captcha found

    if not site_key:
        return False

    # 2. Submit to 2Captcha
    api_key = os.getenv("TWO_CAPTCHA_API_KEY")
    if not api_key:
        return False
        
    response = requests.post("http://2captcha.com/in.php", data={
        "key": api_key,
        "method": "userrecaptcha",
        "googlekey": site_key,
        "pageurl": driver.current_url,
        "json": 1
    })
    request_id = response.json().get("request")
    
    # 3. Poll for Result
    time.sleep(20) # Initial wait
    for _ in range(20): # Max ~120s total
        res = requests.get(f"http://2captcha.com/res.php?key={api_key}&action=get&id={request_id}&json=1")
        result = res.json()
        
        if result.get("status") == 1:
            token = result.get("request")
            
            # 4. Inject Token
            driver.execute_script(f"""
                var el = document.querySelector('[name="g-recaptcha-response"]');
                if (el) {{
                    el.innerHTML = '{token}';
                    el.value = '{token}';
                }}
            """)
            return True
            
        if result.get("request") != "CAPCHA_NOT_READY":
            # Fatal error
            return False
            
        time.sleep(5)
        
    return False
```

## References
*   [2Captcha API: reCAPTCHA V2](https://2captcha.com/api-docs/recaptcha-v2)
*   [2Captcha API: Quick Start](https://2captcha.com/api-docs/quick-start)
