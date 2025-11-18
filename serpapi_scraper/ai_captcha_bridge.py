"""
Bridge utilities for invoking the ai-captcha-bypass helpers with an existing Selenium
WebDriver instance. This keeps the Chrome session managed by our headless scrapers
while delegating visual reasoning to the shared AI utilities that power the CLI.
"""

from __future__ import annotations

import importlib.util
import logging
import os
import random
import sys
import time
from typing import NamedTuple, Optional, Sequence, Tuple
from urllib.parse import parse_qs, urlparse

import requests
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from app.config import PROXY_URL, USER_AGENT

AI_SOLVER_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "ai-captcha-bypass"))
AI_MAIN_PATH = os.path.join(AI_SOLVER_PATH, "main.py")

if AI_SOLVER_PATH not in sys.path:
    sys.path.insert(0, AI_SOLVER_PATH)

_SOLVER_MODULE_NAME = "serpapi_ai_captcha_main"
if _SOLVER_MODULE_NAME in sys.modules:
    solver_module = sys.modules[_SOLVER_MODULE_NAME]
else:
    spec = importlib.util.spec_from_file_location(_SOLVER_MODULE_NAME, AI_MAIN_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load solver module from {AI_MAIN_PATH}")
    solver_module = importlib.util.module_from_spec(spec)
    sys.modules[_SOLVER_MODULE_NAME] = solver_module
    spec.loader.exec_module(solver_module)  # type: ignore[arg-type]

recaptcha_v2_test = getattr(solver_module, "recaptcha_v2_test")

AnchorSelector = Tuple[str, str]

ANCHOR_IFRAME_SELECTORS: Sequence[AnchorSelector] = (
    (By.XPATH, "//iframe[@title='reCAPTCHA']"),
    (By.XPATH, "//iframe[contains(@title, 'reCAPTCHA') and not(contains(@title, 'challenge'))]"),
    (By.CSS_SELECTOR, "iframe[src*='recaptcha']"),
    (By.CSS_SELECTOR, "iframe[title*='reCAPTCHA']"),
)

CAPTCHA_SOLVER_ENV = "CAPTCHA_SOLVER"
CAPTCHA_SOLVER_TWO_CAPTCHA = "2captcha"
CAPTCHA_SOLVER_LEGACY = "legacy"

TWO_CAPTCHA_API_KEY_ENV = "TWO_CAPTCHA_API_KEY"
TWO_CAPTCHA_PROXY_ENV = "TWO_CAPTCHA_PROXY"
TWO_CAPTCHA_PROXY_TYPE_ENV = "TWO_CAPTCHA_PROXY_TYPE"
TWO_CAPTCHA_SUBMIT_URL = "https://2captcha.com/in.php"
TWO_CAPTCHA_RESULT_URL = "https://2captcha.com/res.php"
TWO_CAPTCHA_INITIAL_WAIT = 20
TWO_CAPTCHA_POLL_INTERVAL = 5
TWO_CAPTCHA_TIMEOUT = 120
REQUEST_TIMEOUT = 30


class ProxySettings(NamedTuple):
    address: str
    proxy_type: str

def _normalize_provider(raw: Optional[str]) -> str:
    provider = (raw or os.getenv("AI_CAPTCHA_PROVIDER") or "gemini").strip().lower()
    allowed = {"openai", "gemini", "openrouter", "self-host"}
    if provider not in allowed:
        provider = "gemini"
    return provider


def _provider_model(_provider: str, model: Optional[str]) -> Optional[str]:
    return model or os.getenv("AI_CAPTCHA_MODEL")


def _complex_model_override() -> Optional[str]:
    return os.getenv("AI_CAPTCHA_COMPLEX_MODEL")


def _switch_to_anchor_iframe(driver: WebDriver, selectors: Sequence[AnchorSelector]) -> Optional[AnchorSelector]:
    driver.switch_to.default_content()
    for selector in selectors:
        by, value = selector
        try:
            WebDriverWait(driver, 5).until(
                EC.frame_to_be_available_and_switch_to_it((by, value))
            )
            return selector
        except TimeoutException:
            driver.switch_to.default_content()
            continue
    driver.switch_to.default_content()
    return None


def _verify_anchor_checked(driver: WebDriver, selectors: Sequence[AnchorSelector]) -> bool:
    driver.switch_to.default_content()
    for by, value in selectors:
        try:
            WebDriverWait(driver, 3).until(
                EC.frame_to_be_available_and_switch_to_it((by, value))
            )
            anchor = WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.ID, "recaptcha-anchor"))
            )
            checked = anchor.get_attribute("aria-checked") == "true"
            if checked:
                return True
        except TimeoutException:
            continue
        finally:
            driver.switch_to.default_content()
    return False


def _click_recaptcha_checkbox(driver: WebDriver, logger: logging.Logger) -> bool:
    targets = (
        (By.CLASS_NAME, "recaptcha-checkbox-border"),
        (By.ID, "recaptcha-anchor"),
    )

    for by, value in targets:
        try:
            element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((by, value))
            )
        except TimeoutException:
            continue

        for attempt in range(1, 4):
            try:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                element.click()
                return True
            except ElementClickInterceptedException as exc:
                logger.debug(
                    "Attempt %s to click reCAPTCHA checkbox intercepted: %s",
                    attempt,
                    exc,
                )
                try:
                    driver.execute_script("arguments[0].click();", element)
                    return True
                except Exception:  # pylint: disable=broad-except
                    time.sleep(0.3)
                    continue
            except Exception as exc:  # pylint: disable=broad-except
                logger.debug(
                    "Attempt %s to click reCAPTCHA checkbox failed: %s",
                    attempt,
                    exc,
                )
                time.sleep(0.3)

    try:
        clicked = driver.execute_script(
            """
            const anchor = document.getElementById('recaptcha-anchor')
                || document.querySelector('.recaptcha-checkbox-border');
            if (!anchor) { return false; }
            anchor.scrollIntoView({block: 'center'});
            anchor.click();
            return true;
            """
        )
        if clicked:
            return True
    except Exception as exc:  # pylint: disable=broad-except
        logger.debug("JS-based reCAPTCHA checkbox click failed: %s", exc)

    logger.debug("Unable to click reCAPTCHA checkbox with available strategies")
    return False


def detect_recaptcha(driver: WebDriver) -> bool:
    driver.switch_to.default_content()
    for by, value in ANCHOR_IFRAME_SELECTORS:
        try:
            elements = driver.find_elements(by, value)
        except Exception:  # pylint: disable=broad-except
            continue
        if elements:
            return True
    return False


def _get_captcha_solver() -> str:
    raw = (os.getenv(CAPTCHA_SOLVER_ENV) or CAPTCHA_SOLVER_TWO_CAPTCHA).strip().lower()
    if raw in {"legacy", "legacy-ai", "ai"}:
        return CAPTCHA_SOLVER_LEGACY
    return CAPTCHA_SOLVER_TWO_CAPTCHA


def _resolve_two_captcha_proxy(log: logging.Logger) -> Optional[ProxySettings]:
    raw_proxy = (os.getenv(TWO_CAPTCHA_PROXY_ENV) or PROXY_URL or "").strip()
    if not raw_proxy:
        return None

    try:
        parsed = urlparse(raw_proxy)
    except ValueError as exc:
        log.warning("Invalid proxy URL %s for 2Captcha: %s", raw_proxy, exc)
        return None

    host = parsed.hostname
    port = parsed.port
    if not host or not port:
        log.warning("Proxy URL %s missing host or port for 2Captcha usage", raw_proxy)
        return None

    credentials = ""
    if parsed.username:
        credentials = parsed.username
        if parsed.password:
            credentials += f":{parsed.password}"
        credentials += "@"

    proxy_type = os.getenv(TWO_CAPTCHA_PROXY_TYPE_ENV) or (parsed.scheme or "http")
    proxy_type = proxy_type.upper()
    if proxy_type not in {"HTTP", "HTTPS", "SOCKS4", "SOCKS5"}:
        if proxy_type.startswith("SOCKS5"):
            proxy_type = "SOCKS5"
        elif proxy_type.startswith("SOCKS4"):
            proxy_type = "SOCKS4"
        else:
            proxy_type = "HTTP"

    address = f"{credentials}{host}:{port}"
    log.debug("Using proxy for 2Captcha proxy=%s type=%s", address.rsplit("@", 1)[-1], proxy_type)
    return ProxySettings(address=address, proxy_type=proxy_type)


def _extract_site_details(driver: WebDriver, log: logging.Logger) -> Tuple[Optional[str], Optional[str]]:
    driver.switch_to.default_content()
    selectors = (
        (By.CSS_SELECTOR, ".g-recaptcha[data-sitekey]"),
        (By.CSS_SELECTOR, "[data-sitekey]"),
    )

    for by, value in selectors:
        try:
            elements = driver.find_elements(by, value)
        except Exception as exc:  # pylint: disable=broad-except
            log.debug("Failed querying %s for sitekey: %s", value, exc)
            continue
        for element in elements:
            sitekey = element.get_attribute("data-sitekey")
            if sitekey:
                data_s = element.get_attribute("data-s") or element.get_attribute("data-stoken") or None
                return sitekey, data_s

    try:
        frames = driver.find_elements(By.CSS_SELECTOR, "iframe[src*='recaptcha']")
    except Exception as exc:  # pylint: disable=broad-except
        log.debug("Unable to inspect reCAPTCHA iframes: %s", exc)
        return None, None

    for frame in frames:
        src = frame.get_attribute("src") or ""
        query = urlparse(src).query
        params = parse_qs(query)
        for key in ("k", "render"):
            value = params.get(key)
            if value and value[0]:
                return value[0], None
    return None, None


def _submit_two_captcha_request(
    site_key: str,
    page_url: str,
    api_key: str,
    log: logging.Logger,
    *,
    data_s: Optional[str],
    proxy_settings: Optional[ProxySettings],
) -> Optional[str]:
    payload = {
        "key": api_key,
        "method": "userrecaptcha",
        "googlekey": site_key,
        "pageurl": page_url,
        "json": 1,
        "userAgent": USER_AGENT,
    }
    if data_s:
        payload["data-s"] = data_s
    if proxy_settings:
        payload["proxy"] = proxy_settings.address
        payload["proxytype"] = proxy_settings.proxy_type

    try:
        response = requests.post(TWO_CAPTCHA_SUBMIT_URL, data=payload, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError) as exc:
        log.error("Failed to submit challenge to 2Captcha: %s", exc)
        return None

    if data.get("status") != 1:
        log.error("2Captcha submission error: %s", data.get("request"))
        return None
    return data.get("request")


def _poll_two_captcha_solution(request_id: str, api_key: str, log: logging.Logger) -> Optional[str]:
    time.sleep(TWO_CAPTCHA_INITIAL_WAIT)
    deadline = time.time() + TWO_CAPTCHA_TIMEOUT

    while time.time() < deadline:
        params = {
            "key": api_key,
            "action": "get",
            "id": request_id,
            "json": 1,
        }
        try:
            response = requests.get(TWO_CAPTCHA_RESULT_URL, params=params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
        except (requests.RequestException, ValueError) as exc:
            log.warning("Error polling 2Captcha: %s", exc)
            time.sleep(TWO_CAPTCHA_POLL_INTERVAL)
            continue

        status = data.get("status")
        message = data.get("request")

        if status == 1 and message:
            return message

        if message == "CAPCHA_NOT_READY":
            time.sleep(TWO_CAPTCHA_POLL_INTERVAL)
            continue

        log.error("2Captcha returned terminal error: %s", message)
        return None

    log.error("Timed out waiting for 2Captcha solution (>%ss)", TWO_CAPTCHA_TIMEOUT)
    return None


def _inject_recaptcha_token(driver: WebDriver, token: str, log: logging.Logger) -> bool:
    driver.switch_to.default_content()
    try:
        driver.execute_script(
            """
            const value = arguments[0];
            let textarea = document.querySelector('[name="g-recaptcha-response"]');
            if (!textarea) {
                textarea = document.createElement('textarea');
                textarea.name = 'g-recaptcha-response';
                textarea.style.display = 'none';
                document.body.appendChild(textarea);
            }
            textarea.value = value;
            textarea.innerHTML = value;
            textarea.dispatchEvent(new Event('input', { bubbles: true }));
            textarea.dispatchEvent(new Event('change', { bubbles: true }));
            """,
            token,
        )
        return True
    except Exception as exc:  # pylint: disable=broad-except
        log.exception("Failed to inject 2Captcha token into page: %s", exc)
        return False


def _solve_with_two_captcha(driver: WebDriver, context: str, log: logging.Logger) -> bool:
    site_key, data_s = _extract_site_details(driver, log)
    if not site_key:
        log.warning("(%s) Unable to locate reCAPTCHA sitekey", context)
        return False

    api_key = os.getenv(TWO_CAPTCHA_API_KEY_ENV)
    if not api_key:
        log.error("(%s) %s is not set; cannot solve reCAPTCHA", context, TWO_CAPTCHA_API_KEY_ENV)
        return False

    proxy_settings = _resolve_two_captcha_proxy(log)
    proxy_desc = proxy_settings.address.split("@", 1)[-1] if proxy_settings else "none"
    log.info(
        "(%s) Submitting reCAPTCHA challenge to 2Captcha (sitekey=%s proxy=%s)",
        context,
        site_key[:8] + "...",
        proxy_desc,
    )
    request_id = _submit_two_captcha_request(
        site_key,
        driver.current_url,
        api_key,
        log,
        data_s=data_s,
        proxy_settings=proxy_settings,
    )
    if not request_id:
        return False

    token = _poll_two_captcha_solution(request_id, api_key, log)
    if not token:
        return False

    if not _inject_recaptcha_token(driver, token, log):
        return False

    log.info("(%s) Successfully injected 2Captcha token", context)
    return True


def _solve_with_legacy_ai(
    driver: WebDriver,
    context: str,
    log: logging.Logger,
    provider: Optional[str],
    model: Optional[str],
) -> bool:
    provider_name = _normalize_provider(provider)
    provider_model = _provider_model(provider_name, model)
    complex_model = _complex_model_override()

    anchor_selector = _switch_to_anchor_iframe(driver, ANCHOR_IFRAME_SELECTORS)
    if anchor_selector is None:
        log.debug("(%s) No reCAPTCHA anchor detected", context)
        return True

    try:
        anchor_element = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.ID, "recaptcha-anchor"))
        )
        if anchor_element.get_attribute("aria-checked") == "true":
            log.debug("(%s) reCAPTCHA anchor already checked", context)
            return True
    except TimeoutException:
        pass

    if not _click_recaptcha_checkbox(driver, log):
        driver.switch_to.default_content()
        log.debug("(%s) Failed to click reCAPTCHA checkbox", context)
        return False

    driver.switch_to.default_content()
    log.debug(
        "(%s) Invoking shared solver provider=%s model=%s complex_model=%s",
        context,
        provider_name,
        provider_model or "default",
        complex_model or "none",
    )

    try:
        success = bool(
            recaptcha_v2_test(
                driver,
                provider=provider_name,
                model=provider_model,
                complex_model=complex_model,
                bootstrap_demo=False,
                allow_page_reload=False,
                create_gif_on_success=False,
            )
        )
    except Exception as exc:  # pylint: disable=broad-except
        log.exception("(%s) Solver raised an exception: %s", context, exc)
        driver.switch_to.default_content()
        return False

    driver.switch_to.default_content()
    if not success:
        log.warning("(%s) reCAPTCHA solver could not complete the challenge", context)
        return False

    for _ in range(3):
        if _verify_anchor_checked(driver, ANCHOR_IFRAME_SELECTORS):
            log.info("(%s) reCAPTCHA solved successfully", context)
            return True
        time.sleep(random.uniform(0.6, 1.2))

    log.warning("(%s) Solver reported success but checkbox was not verified", context)
    return False


def solve_recaptcha_if_present(
    driver: WebDriver,
    *,
    context: str,
    logger: Optional[logging.Logger] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> bool:
    """
    Attempt to solve a visible reCAPTCHA v2 challenge in the current page.
    Returns True when no CAPTCHA is present or the challenge is solved.
    """

    log = logger or logging.getLogger("serpapi.ai_captcha")
    if not detect_recaptcha(driver):
        log.debug("(%s) No reCAPTCHA detected on page", context)
        return True

    solver_mode = _get_captcha_solver()
    if solver_mode == CAPTCHA_SOLVER_TWO_CAPTCHA:
        return _solve_with_two_captcha(driver, context, log)

    log.info("(%s) Using legacy AI captcha solver (mode=%s)", context, solver_mode)
    return _solve_with_legacy_ai(driver, context, log, provider, model)
