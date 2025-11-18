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

### A. Infrastructure Changes (Proxy Consistency)
**CRITICAL:** ManualsLib validates that the IP solving the captcha (2Captcha worker) matches the IP submitting the form (our scraper).
Our current setup uses a local Squid proxy (`http://squid:8888`) which round-robins between multiple external upstream proxies. This causes a mismatch because we cannot tell 2Captcha which upstream Squid will pick for the next request.

To fix this, we must enforce a 1:1 mapping between the scraper container and the upstream proxy.

1.  **Modify `squid/squid.conf.template`**:
    *   Expose multiple ports (e.g., 8888, 8889).
    *   Use ACLs to map `port 8888` exclusively to `upstream1`.
    *   Use ACLs to map `port 8889` exclusively to `upstream2`.
    *   Remove `round-robin` configuration.

2.  **Modify `docker-compose.yml`**:
    *   Split the `app` service into `app-group-1` and `app-group-2` (instead of `replicas: 4`).
    *   **App Group 1**:
        *   `PROXY_URL=http://squid:8888` (Internal Squid port for Selenium)
        *   `TWO_CAPTCHA_PROXY=${UPSTREAM_1_PROTO}://${UPSTREAM_1_USER_PASS}@${UPSTREAM_1_HOST}:${UPSTREAM_PROXY_PORT}` (Public upstream for 2Captcha)
    *   **App Group 2**:
        *   `PROXY_URL=http://squid:8889`
        *   `TWO_CAPTCHA_PROXY=${UPSTREAM_2_PROTO}://${UPSTREAM_2_USER_PASS}@${UPSTREAM_2_HOST}:${UPSTREAM_PROXY_PORT}`

### B. Modify `serpapi_scraper/ai_captcha_bridge.py`
We will completely rewrite the implementation of `solve_recaptcha_if_present` to use the 2Captcha API.

1.  **Remove Dependencies:**
    *   Remove imports and logic related to `ai-captcha-bypass` and dynamic module loading.
    *   Remove Selenium interactions that click tiles or checkboxes.

2.  **Implement 2Captcha Logic:**
    *   **Sitekey Extraction:** Extract `data-sitekey` from `.g-recaptcha` or `iframe[src*="recaptcha"]`.
    *   **Data-S Extraction:** Check for the `data-s` attribute on the reCAPTCHA container. This is a one-time token used by some sites (like ManualsLib) for extra verification and **must** be passed to 2Captcha if present.
    *   **API Submission:**
        *   Send `sitekey`, `pageurl`, `userAgent`, and `data-s` (if found).
        *   **Proxy Handling:** Check for `TWO_CAPTCHA_PROXY` environment variable.
            *   If present, parse it into `proxy` (`login:pass@ip:port`) and `proxytype` (`HTTP`).
            *   If absent, fall back to `PROXY_URL` (only if it's not a local/internal proxy).
            *   **Fail-safe:** If no valid public proxy is available, log a warning (ManualsLib will likely reject the token).
    *   **Polling:** Poll `res.php` every 5 seconds (after initial 20s delay) until success or timeout (120s).
    *   **Token Injection:** Inject the response token into `[name="g-recaptcha-response"]`.

3.  **Environment Configuration:**
    *   `TWO_CAPTCHA_API_KEY`: Required.
    *   `TWO_CAPTCHA_PROXY`: Required for IP consistency (set in docker-compose).
    *   `CAPTCHA_SOLVER`: Defaults to `2captcha`. Set to `legacy` to rollback.
    *   Refer to `docs/manualslib_proxy_strategy.md` for the multi-proxy/Squid layout and container-to-proxy assignment details.

## 3. Step-by-Step Implementation Plan

1.  **Infrastructure Prep**:
    *   Update `squid/squid.conf.template` to support port-based routing.
    *   Update `docker-compose.yml` to define `app-group-1` and `app-group-2` with correct env vars.

2.  **Update `serpapi_scraper/ai_captcha_bridge.py`**:
    *   Implement `solve_recaptcha_v2` with 2Captcha API integration.
    *   Add logic to parse `TWO_CAPTCHA_PROXY`.
    *   Add logic to extract `data-s`.

3.  **Testing**:
    *   Verify that `manualslib_scraper.py` successfully downloads manuals.
    *   Check logs to ensure `proxy` is being sent to 2Captcha and matches the upstream used by Squid.

## 4. Code Snippet for `ai_captcha_bridge.py` (Preview)

```python
import time
import requests
import os
from urllib.parse import urlparse
from app.config import PROXY_URL, USER_AGENT

def format_proxy_for_2captcha(proxy_url):
    """Convert http://user:pass@host:port to user:pass@host:port"""
    try:
        parsed = urlparse(proxy_url)
        return f"{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port}"
    except Exception:
        return None

def solve_recaptcha_if_present(driver: WebDriver, ...) -> bool:
    # ... (sitekey & data-s extraction) ...

    api_key = os.getenv("TWO_CAPTCHA_API_KEY")
    public_proxy = os.getenv("TWO_CAPTCHA_PROXY")
    
    payload = {
        "key": api_key,
        "method": "userrecaptcha",
        "googlekey": site_key,
        "pageurl": driver.current_url,
        "json": 1,
        "userAgent": USER_AGENT
    }
    
    if data_s:
        payload["data-s"] = data_s

    if public_proxy:
        payload["proxy"] = format_proxy_for_2captcha(public_proxy)
        payload["proxytype"] = "HTTP"
    else:
        # Fallback or warning if using local proxy
        pass

    # ... (submit & poll) ...
```

## References
*   [2Captcha API: reCAPTCHA V2](https://2captcha.com/api-docs/recaptcha-v2)
*   [2Captcha API: Quick Start](https://2captcha.com/api-docs/quick-start)
