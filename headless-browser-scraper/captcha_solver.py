import logging
import os
import random
import re
import time
from collections import namedtuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Iterable, List, Optional, Set, Tuple

from PIL import Image
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from ai_utils import (
    ask_if_tile_contains_object_gemini,
    ask_recaptcha_instructions_to_gemini,
)

TileInfo = namedtuple("TileInfo", ["index", "element", "llm_path"])


class CaptchaSolver:
    """Solve reCAPTCHA v2 challenges using Gemini for vision classification."""

    def __init__(self, driver, model: str = "gemini-2.5-pro") -> None:
        self.driver = driver
        self.model = model
        self.screenshot_dir = "headless-browser-scraper/screenshots"
        self.success_dir = "headless-browser-scraper/successful_solves"
        os.makedirs(self.screenshot_dir, exist_ok=True)
        os.makedirs(self.success_dir, exist_ok=True)
        self.logger = logging.getLogger("headless.captcha_solver")

    # ------------------------------------------------------------------ #
    # Detection
    # ------------------------------------------------------------------ #
    def detect_type(self) -> Optional[str]:
        selectors = [
            (By.CSS_SELECTOR, "#rc-anchor-container", "#rc-anchor-container"),
            (By.CSS_SELECTOR, ".recaptcha-checkbox", ".recaptcha-checkbox"),
            (By.XPATH, "//div[@id='rc-anchor-container']", "//div[@id='rc-anchor-container']"),
            (By.XPATH, "//span[@id='recaptcha-anchor']", "//span[@id='recaptcha-anchor']"),
            (By.ID, "recaptcha-anchor", "recaptcha-anchor"),
        ]

        def _check_current_context() -> Optional[str]:
            for by, value, label in selectors:
                try:
                    elements = self.driver.find_elements(by, value)
                except Exception as exc:  # pylint: disable=broad-except
                    self.logger.debug("Selector %s raised %s", label, exc)
                    continue
                if elements:
                    self.logger.debug(
                        "Found reCAPTCHA selector %s (%d matches)", label, len(elements)
                    )
                    return label
            return None

        self.logger.debug("Running CAPTCHA detection on %s", self.driver.current_url)
        try:
            match = _check_current_context()
            if match:
                self.logger.info("Detected reCAPTCHA v2 via selector %s", match)
                return "recaptcha_v2"

            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            self.logger.debug("Scanning %d iframe(s) for reCAPTCHA", len(iframes))
            for idx, frame in enumerate(iframes):
                try:
                    self.driver.switch_to.frame(frame)
                    match = _check_current_context()
                    if match:
                        self.logger.info(
                            "Detected reCAPTCHA v2 in iframe[%d] via selector %s", idx, match
                        )
                        return "recaptcha_v2"
                except Exception as exc:  # pylint: disable=broad-except
                    self.logger.debug("Error inspecting iframe[%d]: %s", idx, exc)
                finally:
                    self.driver.switch_to.default_content()
        finally:
            self.driver.switch_to.default_content()

        self.logger.debug("No CAPTCHA detected on current page")
        return None

    # ------------------------------------------------------------------ #
    # Solving
    # ------------------------------------------------------------------ #
    def solve_recaptcha_v2(self, max_retries: int = 3) -> bool:
        """
        Solve image challenges surfaced by reCAPTCHA v2. The implementation follows
        the multi-round strategy from the ai-captcha-bypass reference: capture
        instructions, classify tiles in parallel, avoid re-clicking tiles that were
        already marked, and retry when Google refreshes images.
        """
        screenshot_paths: List[str] = []
        try:
            for attempt in range(1, max_retries + 1):
                self.logger.info("reCAPTCHA v2 solve attempt %d/%d", attempt, max_retries)
                self.driver.switch_to.default_content()

                checkbox_checked = self._click_recaptcha_checkbox()
                challenge_attached = self._switch_to_challenge_iframe(timeout=6)

                if not challenge_attached:
                    if checkbox_checked and self._verify_anchor_checked(timeout=4):
                        self.logger.info(
                            "Attempt %d: Checkbox verified without challenge", attempt
                        )
                        self._create_success_gif(screenshot_paths)
                        return True

                    self.logger.debug(
                        "Attempt %d: No challenge iframe detected, retrying after short pause",
                        attempt,
                    )
                    time.sleep(1.5)
                    continue

                clicked_tile_indices: Set[int] = set()
                last_object_name = ""
                last_click_count = 0
                challenge_success = False

                MAX_CHALLENGE_ROUNDS = 5
                for round_index in range(1, MAX_CHALLENGE_ROUNDS + 1):
                    if not self._switch_to_challenge_iframe(timeout=3):
                        self.logger.debug("Challenge iframe vanished; checking checkbox state.")
                        if self._verify_anchor_checked(timeout=4):
                            challenge_success = True
                        break

                    self.logger.info(
                        "Attempt %d: challenge round %d", attempt, round_index
                    )

                    try:
                        challenge_path, challenge_llm_path = self._capture_challenge_state(
                            attempt, round_index, screenshot_paths
                        )

                        instruction_element = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located(
                                (By.CLASS_NAME, "rc-imageselect-instructions")
                            )
                        )
                        object_name = self._determine_target_object(
                            attempt,
                            round_index,
                            instruction_element,
                            screenshot_paths,
                        )
                    except TimeoutException:
                        self.logger.debug(
                            "Attempt %d round %d: challenge elements vanished mid-run",
                            attempt,
                            round_index,
                        )
                        if self._verify_anchor_checked(timeout=4):
                            challenge_success = True
                        break

                    if not object_name:
                        self.logger.warning(
                            "Attempt %d round %d: Unable to determine challenge instruction",
                            attempt,
                            round_index,
                        )
                        break

                    if object_name == "skip":
                        self.logger.info(
                            "Attempt %d round %d: instruction requested skip; reloading challenge",
                            attempt,
                            round_index,
                        )
                        self._click_skip_button()
                        clicked_tile_indices.clear()
                        last_object_name = ""
                        last_click_count = 0
                        time.sleep(1.5)
                        continue

                    is_new_object = object_name.lower() != last_object_name.lower()
                    if is_new_object or last_click_count >= 3:
                        clicked_tile_indices.clear()
                        if is_new_object:
                            self.logger.debug(
                                "Attempt %d round %d: new target '%s'; resetting clicked tiles",
                                attempt,
                                round_index,
                                object_name,
                            )
                        else:
                            self.logger.debug(
                                "Attempt %d round %d: same object but >=3 new clicks last round; resetting clicked tiles",
                                attempt,
                                round_index,
                            )
                    last_object_name = object_name

                    tiles, tile_infos = self._collect_tiles(
                        attempt, round_index, screenshot_paths
                    )
                    if not tiles:
                        self.logger.warning(
                            "Attempt %d round %d: no tiles located inside challenge grid",
                            attempt,
                            round_index,
                        )
                        break

                    selected_indices = self._classify_tiles_parallel(
                        attempt,
                        round_index,
                        tile_infos,
                        object_name,
                        challenge_llm_path,
                    )

                    new_tiles = sorted(idx for idx in selected_indices if idx not in clicked_tile_indices)
                    self.logger.info(
                        "Attempt %d round %d: AI selected tiles %s (new clicks: %s)",
                        attempt,
                        round_index,
                        sorted(list(selected_indices)),
                        new_tiles,
                    )

                    last_click_count = len(new_tiles)
                    self._click_tiles(tiles, new_tiles)
                    clicked_tile_indices.update(new_tiles)

                    if self._verify_challenge_success():
                        self.driver.switch_to.default_content()
                        if self._verify_anchor_checked(timeout=6):
                            challenge_success = True
                            break

                    # We are likely served new tiles; allow DOM to update before next pass.
                    self.driver.switch_to.default_content()
                    time.sleep(2)

                if challenge_success:
                    self.logger.info("Attempt %d: reCAPTCHA challenge solved", attempt)
                    self._create_success_gif(screenshot_paths)
                    return True

                self.logger.warning("Attempt %d: challenge not solved; retrying", attempt)
                time.sleep(2)

            self.logger.error("All %d reCAPTCHA attempts failed", max_retries)
            self._create_success_gif(screenshot_paths, success=False)
            return False
        finally:
            self.driver.switch_to.default_content()

    # ------------------------------------------------------------------ #
    # Tile capture & classification helpers
    # ------------------------------------------------------------------ #
    def _capture_challenge_state(
        self,
        attempt: int,
        round_index: int,
        screenshot_paths: List[str],
    ) -> Tuple[str, str]:
        target_element = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "rc-imageselect-target"))
        )
        challenge_path = os.path.join(
            self.screenshot_dir, f"challenge_target_{attempt}_{round_index}.png"
        )
        target_element.screenshot(challenge_path)
        screenshot_paths.append(challenge_path)
        llm_path = self._prepare_image_for_llm(
            challenge_path, suffix=f"challenge_{attempt}_{round_index}"
        )
        return challenge_path, llm_path

    def _determine_target_object(
        self,
        attempt: int,
        round_index: int,
        instruction_element,
        screenshot_paths: List[str],
    ) -> Optional[str]:
        instruction_text = instruction_element.text.strip()
        dom_object = self._parse_instruction_text(instruction_text)
        if dom_object:
            self.logger.debug(
                "Attempt %d round %d: DOM instruction text => %s",
                attempt,
                round_index,
                dom_object,
            )

        instruction_path = os.path.join(
            self.screenshot_dir, f"instruction_{attempt}_{round_index}.png"
        )
        instruction_element.screenshot(instruction_path)
        screenshot_paths.append(instruction_path)

        try:
            gemini_object = ask_recaptcha_instructions_to_gemini(
                instruction_path, self.model
            )
            if dom_object and gemini_object and dom_object.lower() != gemini_object.lower():
                self.logger.info(
                    "Attempt %d round %d: DOM instruction '%s' differs from Gemini '%s'; using Gemini result",
                    attempt,
                    round_index,
                    dom_object,
                    gemini_object,
                )
            else:
                self.logger.info(
                    "Attempt %d round %d: target object (Gemini) => %s",
                    attempt,
                    round_index,
                    gemini_object,
                )
            return gemini_object or dom_object
        except Exception as exc:  # pylint: disable=broad-except
            self.logger.warning(
                "Attempt %d round %d: failed to extract instruction via Gemini: %s",
                attempt,
                round_index,
                exc,
            )
            return dom_object

    def _collect_tiles(
        self,
        attempt: int,
        round_index: int,
        screenshot_paths: List[str],
    ) -> Tuple[List, List[TileInfo]]:
        try:
            table = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//table[contains(@class, 'rc-imageselect-table')]")
                )
            )
        except TimeoutException:
            return [], []

        tiles = table.find_elements(By.TAG_NAME, "td")
        tile_infos: List[TileInfo] = []
        for idx, tile in enumerate(tiles):
            tile_path = os.path.join(
                self.screenshot_dir, f"tile_{attempt}_{round_index}_{idx}.png"
            )
            tile.screenshot(tile_path)
            screenshot_paths.append(tile_path)
            llm_path = self._prepare_image_for_llm(
                tile_path, suffix=f"tile_{attempt}_{round_index}_{idx}"
            )
            tile_infos.append(TileInfo(index=idx, element=tile, llm_path=llm_path))
        return tiles, tile_infos

    def _classify_tiles_parallel(
        self,
        attempt: int,
        round_index: int,
        tile_infos: Iterable[TileInfo],
        object_name: str,
        challenge_llm_path: str,
    ) -> Set[int]:
        indices: Set[int] = set()
        tile_infos_list = list(tile_infos)
        if not tile_infos_list:
            return indices

        max_workers = max(1, len(tile_infos_list))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    self._classify_tile,
                    attempt,
                    info.index,
                    info.llm_path,
                    object_name,
                    challenge_llm_path,
                    round_index,
                ): info.index
                for info in tile_infos_list
            }
            for future in as_completed(futures):
                tile_index, response = future.result()
                if response == "true":
                    indices.add(tile_index)
        return indices

    def _classify_tile(
        self,
        attempt_number: int,
        tile_index: int,
        image_path: str,
        object_name: str,
        context_path: Optional[str] = None,
        round_number: int = 0,
    ) -> Tuple[int, Optional[str]]:
        try:
            response = ask_if_tile_contains_object_gemini(
                image_path,
                object_name,
                self.model,
                context_image_path=context_path,
            )
            self.logger.info(
                "Attempt %d round %d tile %d Gemini classification: %s",
                attempt_number,
                round_number,
                tile_index,
                response,
            )
            return tile_index, response
        except Exception as exc:  # pylint: disable=broad-except
            self.logger.warning(
                "Attempt %d round %d tile %d classification failed: %s",
                attempt_number,
                round_number,
                tile_index,
                exc,
            )
            return tile_index, None

    def _click_tiles(self, tiles: List, tile_indices: Iterable[int]) -> None:
        for idx in tile_indices:
            try:
                tile = tiles[idx]
            except IndexError:
                continue
            try:
                if tile.is_displayed() and tile.is_enabled():
                    tile.click()
                    time.sleep(random.uniform(0.2, 0.5))
            except (StaleElementReferenceException, Exception) as exc:  # pylint: disable=broad-except
                self.logger.debug("Failed to click tile %d: %s", idx, exc)

    # ------------------------------------------------------------------ #
    # Verification helpers
    # ------------------------------------------------------------------ #
    def _verify_challenge_success(self) -> bool:
        try:
            verify_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.ID, "recaptcha-verify-button"))
            )
        except TimeoutException:
            self.logger.debug("Verify button not available; assuming challenge closed.")
            return self._verify_anchor_checked(timeout=4)

        try:
            verify_button.click()
        except Exception as exc:  # pylint: disable=broad-except
            self.logger.debug("Verify button click failed: %s", exc)
            return False

        time.sleep(random.uniform(1.0, 1.6))
        try:
            if verify_button.get_attribute("disabled"):
                self.logger.info("Verify button disabled after click; challenge likely solved.")
                return True
        except StaleElementReferenceException:
            self.logger.debug("Verify button detached after click; treating as success signal.")
            return True

        self.logger.debug("Verify button still active; challenge may have refreshed.")
        return False

    def _verify_anchor_checked(self, timeout: int = 3) -> bool:
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.frame_to_be_available_and_switch_to_it(
                    (
                        By.XPATH,
                        "//iframe[contains(@title, 'reCAPTCHA') and not(contains(@title, 'challenge'))]",
                    )
                )
            )
            anchor = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.ID, "recaptcha-anchor"))
            )
            state = anchor.get_attribute("aria-checked") == "true"
            self.logger.debug("Anchor verification state => %s", state)
            return state
        except TimeoutException:
            return False
        finally:
            self.driver.switch_to.default_content()

    # ------------------------------------------------------------------ #
    # Browser helpers & utilities
    # ------------------------------------------------------------------ #
    def _click_recaptcha_checkbox(self) -> bool:
        """Click the reCAPTCHA checkbox via JS to avoid overlay interception."""
        try:
            WebDriverWait(self.driver, 5).until(
                EC.frame_to_be_available_and_switch_to_it(
                    (
                        By.XPATH,
                        "//iframe[contains(@title, 'reCAPTCHA') and not(contains(@title, 'challenge'))]",
                    )
                )
            )
            checkbox = WebDriverWait(self.driver, 5).until(
                EC.presence_of_element_located((By.ID, "recaptcha-anchor"))
            )
            state = checkbox.get_attribute("aria-checked")
            if state == "true":
                self.logger.info("reCAPTCHA checkbox already checked")
                return True
            self.driver.execute_script("arguments[0].click();", checkbox)
            time.sleep(random.uniform(0.6, 1.2))
            state_after = checkbox.get_attribute("aria-checked")
            if state_after == "true":
                self.logger.info("Clicked reCAPTCHA checkbox via JS")
                return True
            self.logger.debug("Checkbox state after click attempt remained %s", state_after)
            return False
        except TimeoutException:
            self.logger.debug("Anchor iframe not available for checkbox click")
            return False
        except Exception as exc:  # pylint: disable=broad-except
            self.logger.warning("Error clicking reCAPTCHA checkbox: %s", exc)
            return False
        finally:
            self.driver.switch_to.default_content()

    def _switch_to_challenge_iframe(self, timeout: int = 3) -> bool:
        """Attempt to switch into the challenge iframe if it is present."""
        try:
            challenge_iframe = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//iframe[contains(@src, 'recaptcha') and contains(@title, 'challenge')]",
                    )
                )
            )
            self.driver.switch_to.frame(challenge_iframe)
            self.logger.debug("Challenge iframe detected")
            return True
        except TimeoutException:
            return False

    def _parse_instruction_text(self, instruction_text: str) -> Optional[str]:
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
                target = target.replace("'", " ").strip()
                return target
        if "click skip" in lower:
            return "skip"
        return None

    def _click_skip_button(self) -> None:
        try:
            skip_button = WebDriverWait(self.driver, 3).until(
                EC.element_to_be_clickable((By.ID, "recaptcha-reload-button"))
            )
            skip_button.click()
        except Exception as exc:  # pylint: disable=broad-except
            self.logger.debug("Skip button click failed: %s", exc)

    def _prepare_image_for_llm(self, image_path: str, suffix: str = "processed") -> str:
        """Downscale and convert screenshots for faster LLM uploads."""
        try:
            with Image.open(image_path) as img:
                max_dim = 512
                if max(img.size) > max_dim:
                    img.thumbnail((max_dim, max_dim))
                optimized_path = os.path.splitext(image_path)[0] + f"_{suffix}.jpg"
                img.convert("RGB").save(optimized_path, format="JPEG", quality=85)
                return optimized_path
        except Exception as exc:  # pylint: disable=broad-except
            self.logger.debug(
                "Unable to optimize image %s for LLM consumption: %s",
                image_path,
                exc,
            )
            return image_path

    def _create_success_gif(self, image_paths: Iterable[str], success: bool = True) -> None:
        image_paths = list(image_paths)
        if not image_paths:
            return

        valid_images = [
            Image.open(path).convert("RGB")
            for path in image_paths
            if os.path.exists(path)
        ]
        if not valid_images:
            return

        max_width = max(img.width for img in valid_images)
        max_height = max(img.height for img in valid_images)
        processed = []
        for img in valid_images:
            canvas = Image.new("RGB", (max_width, max_height), (255, 255, 255))
            pos = ((max_width - img.width) // 2, (max_height - img.height) // 2)
            canvas.paste(img, pos)
            processed.append(canvas)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        status = "success" if success else "fail"
        output = os.path.join(
            self.success_dir, f"recaptcha_{status}_{timestamp}.gif"
        )
        processed[0].save(
            output,
            save_all=True,
            append_images=processed[1:],
            duration=800,
            loop=0,
        )
