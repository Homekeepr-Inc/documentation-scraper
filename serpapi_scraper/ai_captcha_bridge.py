"""
Bridge utilities for invoking the ai-captcha-bypass helpers with an existing Selenium
WebDriver instance. This keeps the Chrome session managed by our headless scrapers
while delegating visual reasoning to the shared AI utilities.
"""

from __future__ import annotations

import importlib.util
import logging
import os
import random
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Iterable, List, Optional, Sequence, Set, Tuple

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
    NoSuchElementException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

AI_SOLVER_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "ai-captcha-bypass"))
AI_UTILS_PATH = os.path.join(AI_SOLVER_PATH, "ai_utils.py")

if "serpapi_ai_captcha_ai_utils" in sys.modules:
    ai_utils = sys.modules["serpapi_ai_captcha_ai_utils"]  # type: ignore[assignment]
else:
    spec = importlib.util.spec_from_file_location("serpapi_ai_captcha_ai_utils", AI_UTILS_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load ai_utils from {AI_UTILS_PATH}")
    ai_utils = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = ai_utils
    spec.loader.exec_module(ai_utils)  # type: ignore[arg-type]

ask_if_tile_contains_object_chatgpt = getattr(ai_utils, "ask_if_tile_contains_object_chatgpt")
ask_if_tile_contains_object_gemini = getattr(ai_utils, "ask_if_tile_contains_object_gemini")
ask_recaptcha_instructions_to_chatgpt = getattr(ai_utils, "ask_recaptcha_instructions_to_chatgpt")
ask_recaptcha_instructions_to_gemini = getattr(ai_utils, "ask_recaptcha_instructions_to_gemini")


AnchorSelector = Tuple[str, str]


ANCHOR_IFRAME_SELECTORS: Sequence[AnchorSelector] = (
    (By.XPATH, "//iframe[@title='reCAPTCHA']"),
    (By.XPATH, "//iframe[contains(@title, 'reCAPTCHA') and not(contains(@title, 'challenge'))]"),
    (By.CSS_SELECTOR, "iframe[src*='recaptcha']"),
    (By.CSS_SELECTOR, "iframe[title*='reCAPTCHA']"),
)

CHALLENGE_IFRAME_SELECTORS: Sequence[AnchorSelector] = (
    (By.XPATH, "//iframe[contains(@title, 'recaptcha challenge')]"),
    (By.CSS_SELECTOR, "iframe[src*='bframe']"),
)


def _screenshots_dir() -> str:
    base_dir = os.path.join(os.path.dirname(__file__), "ai-captcha-bypass", "screenshots")
    os.makedirs(base_dir, exist_ok=True)
    return base_dir


def _normalize_provider(raw: Optional[str]) -> str:
    provider = (raw or os.getenv("AI_CAPTCHA_PROVIDER") or "gemini").strip().lower()
    if provider not in {"openai", "gemini"}:
        provider = "gemini"
    return provider


def _provider_model(provider: str, model: Optional[str]) -> Optional[str]:
    return model or os.getenv("AI_CAPTCHA_MODEL")


def _parse_instruction_text(instruction_text: str) -> Optional[str]:
    if not instruction_text:
        return None
    lower = instruction_text.lower().replace("\n", " ")
    patterns = [
        r"select all (?:squares|images) (?:that )?contain(?: a| an)? ([^\.]+)",
        r"select all (?:squares|images) with ([^\.]+)",
        r"click all images with ([^\.]+)",
        r"click all squares with ([^\.]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, lower)
        if match:
            target = match.group(1)
            target = target.split(" if ")[0]
            target = target.split(" otherwise ")[0]
            target = target.split(" then ")[0]
            target = re.sub(r"\s*click.*", "", target)
            return target.strip()
    if "click skip" in lower or "press skip" in lower:
        return "skip"
    return None


def _capture_instruction(
    driver: WebDriver,
    screenshot_dir: str,
    attempt: int,
    context: str,
) -> Tuple[str, str]:
    instruction_element = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "rc-imageselect-instructions"))
    )
    instruction_path = os.path.join(
        screenshot_dir, f"{context.replace(' ', '_')}_instruction_{attempt}.png"
    )
    instruction_element.screenshot(instruction_path)
    return instruction_path, instruction_element.text.strip()


def _collect_tiles(
    driver: WebDriver,
    screenshot_dir: str,
    attempt: int,
    context: str,
) -> List[Tuple[int, str, WebElement]]:
    table = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//table[contains(@class, 'rc-imageselect-table')]"))
    )
    tiles = table.find_elements(By.TAG_NAME, "td")
    tile_infos: List[Tuple[int, str, WebElement]] = []
    for idx, tile in enumerate(tiles):
        path = os.path.join(
            screenshot_dir,
            f"{context.replace(' ', '_')}_tile_{attempt}_{idx}.png",
        )
        tile.screenshot(path)
        tile_infos.append((idx, path, tile))
    return tile_infos


def _classify_tile(
    tile_path: str,
    object_name: str,
    provider: str,
    model: Optional[str],
) -> bool:
    try:
        if provider == "openai":
            decision = ask_if_tile_contains_object_chatgpt(tile_path, object_name, model)
        else:
            decision = ask_if_tile_contains_object_gemini(tile_path, object_name, model)
    except Exception:
        return False
    normalized = (decision or "").strip().lower()
    if normalized in {"true", "yes", "y"}:
        return True
    if normalized in {"false", "no", "n"}:
        return False
    return normalized.startswith("true")


def _classify_tiles(
    tile_infos: Iterable[Tuple[int, str, WebElement]],
    object_name: str,
    provider: str,
    model: Optional[str],
) -> List[int]:
    tile_list = list(tile_infos)
    if not tile_list:
        return []

    def _task(info: Tuple[int, str, WebElement]) -> Tuple[int, bool]:
        idx, path, _ = info
        return idx, _classify_tile(path, object_name, provider, model)

    max_workers = min(len(tile_list), 6) or 1
    results: List[Tuple[int, bool]]
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(_task, tile_list))

    return [idx for idx, should_click in results if should_click]


def _click_tiles(
    tiles: List[Tuple[int, str, WebElement]],
    indices: Iterable[int],
    logger: logging.Logger,
) -> None:
    for idx in sorted(indices):
        try:
            tile_element = tiles[idx][2]
        except IndexError:
            continue
        try:
            if tile_element.is_displayed() and tile_element.is_enabled():
                tile_element.click()
                time.sleep(random.uniform(0.25, 0.55))
        except (ElementClickInterceptedException, ElementNotInteractableException) as exc:
            logger.debug("Tile %d click failed: %s", idx, exc)


def _click_skip_button(driver: WebDriver, logger: logging.Logger) -> None:
    try:
        skip_button = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.ID, "recaptcha-reload-button"))
        )
        skip_button.click()
    except TimeoutException:
        logger.debug("Skip button not available; continuing.")


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


def _click_recaptcha_checkbox(driver: WebDriver, logger: logging.Logger) -> bool:
    try:
        checkbox = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "recaptcha-checkbox-border"))
        )
        checkbox.click()
        return True
    except TimeoutException:
        try:
            anchor = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.ID, "recaptcha-anchor"))
            )
            anchor.click()
            return True
        except TimeoutException:
            logger.debug("Unable to click reCAPTCHA checkbox")
            return False
    except ElementClickInterceptedException as exc:
        logger.debug("Checkbox click intercepted: %s", exc)
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
    max_challenge_attempts: int = 5,
) -> bool:
    """
    Attempt to solve a visible reCAPTCHA v2 challenge in the current page.
    Returns True when no CAPTCHA is present or the challenge is solved.
    """

    log = logger or logging.getLogger("serpapi.ai_captcha")
    provider_name = _normalize_provider(provider)
    provider_model = _provider_model(provider_name, model)
    screenshot_dir = _screenshots_dir()

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
    clicked_tile_indices: Set[int] = set()
    last_object_name = ""
    last_click_count = 0

    for attempt in range(1, max_challenge_attempts + 1):
        challenge_iframe = None
        for selector in CHALLENGE_IFRAME_SELECTORS:
            by, value = selector
            try:
                WebDriverWait(driver, 4).until(
                    EC.frame_to_be_available_and_switch_to_it((by, value))
                )
                challenge_iframe = selector
                break
            except TimeoutException:
                driver.switch_to.default_content()
                continue

        if challenge_iframe is None:
            if _verify_anchor_checked(driver, ANCHOR_IFRAME_SELECTORS):
                log.info("(%s) reCAPTCHA solved after %d attempt(s)", context, attempt - 1)
                return True
            time.sleep(1.0)
            continue

        try:
            instruction_path, raw_instruction = _capture_instruction(driver, screenshot_dir, attempt, context)
            object_name = _parse_instruction_text(raw_instruction)
            if not object_name:
                if provider_name == "openai":
                    object_name = ask_recaptcha_instructions_to_chatgpt(instruction_path, provider_model)
                else:
                    object_name = ask_recaptcha_instructions_to_gemini(instruction_path, provider_model)
            object_name = (object_name or "").strip()
            if not object_name:
                log.debug("(%s) Could not determine target object on attempt %d", context, attempt)
                driver.switch_to.default_content()
                time.sleep(1.0)
                continue

            log.debug("(%s) Attempt %d target object => %s", context, attempt, object_name)

            if object_name.lower() == "skip":
                _click_skip_button(driver, log)
                driver.switch_to.default_content()
                clicked_tile_indices.clear()
                last_object_name = ""
                last_click_count = 0
                time.sleep(1.2)
                continue

            tiles = _collect_tiles(driver, screenshot_dir, attempt, context)
            tile_indices = _classify_tiles(tiles, object_name, provider_name, provider_model)
            current_indices = set(tile_indices)
            if object_name.lower() != last_object_name.lower() or last_click_count >= 3:
                clicked_tile_indices.clear()
            new_indices = sorted(current_indices - clicked_tile_indices)
            last_object_name = object_name
            last_click_count = len(new_indices)

            log.debug("(%s) Attempt %d AI selected tiles: %s", context, attempt, sorted(tile_indices))
            _click_tiles(tiles, new_indices, log)
            clicked_tile_indices.update(new_indices)

            try:
                verify_button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.ID, "recaptcha-verify-button"))
                )
                verify_button.click()
                time.sleep(1.5)

                try:
                    verify_button_post = driver.find_element(By.ID, "recaptcha-verify-button")
                    if verify_button_post.get_attribute("disabled"):
                        driver.switch_to.default_content()
                        if _verify_anchor_checked(driver, ANCHOR_IFRAME_SELECTORS):
                            log.info("(%s) reCAPTCHA solved successfully", context)
                            return True
                except NoSuchElementException:
                    driver.switch_to.default_content()
                    if _verify_anchor_checked(driver, ANCHOR_IFRAME_SELECTORS):
                        log.info("(%s) reCAPTCHA solved successfully", context)
                        return True
            except TimeoutException:
                driver.switch_to.default_content()
                if _verify_anchor_checked(driver, ANCHOR_IFRAME_SELECTORS):
                    log.info("(%s) reCAPTCHA solved successfully", context)
                    return True
                time.sleep(1.0)
                continue
        finally:
            driver.switch_to.default_content()
            time.sleep(1.0)

    success = _verify_anchor_checked(driver, ANCHOR_IFRAME_SELECTORS)
    if success:
        log.info("(%s) reCAPTCHA solved after max attempts", context)
    else:
        log.warning("(%s) Failed to solve reCAPTCHA after %d attempts", context, max_challenge_attempts)
    return success
