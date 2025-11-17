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
from typing import Optional, Sequence, Tuple

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

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

    # Wait briefly for the checkbox state to propagate.
    for _ in range(3):
        if _verify_anchor_checked(driver, ANCHOR_IFRAME_SELECTORS):
            log.info("(%s) reCAPTCHA solved successfully", context)
            return True
        time.sleep(random.uniform(0.6, 1.2))

    log.warning("(%s) Solver reported success but checkbox was not verified", context)
    return False
