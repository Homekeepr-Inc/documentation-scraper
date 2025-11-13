import logging
import os
import random
import re
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Set, List, Tuple

from PIL import Image
import imageio
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.wait import WebDriverWait as Wait  # Alias if needed

from ai_utils import (
    ask_recaptcha_instructions_to_gemini,
    ask_if_tile_contains_object_gemini,
    ask_text_to_gemini
)


class CaptchaSolver:
    def __init__(self, driver, model='gemini-2.5-pro'):
        self.driver = driver
        self.model = model
        self.screenshot_dir = 'headless-browser-scraper/screenshots'
        self.success_dir = 'headless-browser-scraper/successful_solves'
        os.makedirs(self.screenshot_dir, exist_ok=True)
        os.makedirs(self.success_dir, exist_ok=True)
        self.logger = logging.getLogger("headless.captcha_solver")

    def detect_type(self):
        selectors = [
            (By.CSS_SELECTOR, "#rc-anchor-container", "#rc-anchor-container"),
            (By.CSS_SELECTOR, ".recaptcha-checkbox", ".recaptcha-checkbox"),
            (By.XPATH, "//div[@id='rc-anchor-container']", "//div[@id='rc-anchor-container']"),
            (By.XPATH, "//span[@id='recaptcha-anchor']", "//span[@id='recaptcha-anchor']"),
            (By.ID, "recaptcha-anchor", "recaptcha-anchor"),
        ]

        def _check_current_context():
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
                return 'recaptcha_v2'

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
                        return 'recaptcha_v2'
                except Exception as exc:  # pylint: disable=broad-except
                    self.logger.debug("Error inspecting iframe[%d]: %s", idx, exc)
                finally:
                    self.driver.switch_to.default_content()
        finally:
            self.driver.switch_to.default_content()

        self.logger.debug("No CAPTCHA detected on current page")
        return None

    def solve_recaptcha_v2(self, max_rounds=5):
        """Solve reCAPTCHA v2 by persistently handling challenges until completion or max rounds reached."""
        screenshot_paths = []
        total_rounds = 0
        clicked_tile_indices: Set[int] = set()
        last_object_name = ""
        last_click_count = 0

        try:
            self.logger.info("Starting reCAPTCHA v2 solve with max %d rounds", max_rounds)

            # Ensure we're in default content
            self.driver.switch_to.default_content()

            # Click checkbox to trigger challenge
            checkbox_checked = self._click_recaptcha_checkbox()
            if not checkbox_checked:
                self.logger.warning("Failed to click checkbox; aborting solve")
                return False

            # Persistent loop: handle challenges until iframe disappears or max rounds
            while total_rounds < max_rounds:
                total_rounds += 1
                self.logger.info("Challenge round %d/%d", total_rounds, max_rounds)

                # Switch to challenge iframe if present
                if not self._switch_to_challenge_iframe(timeout=5):
                    self.logger.info("No challenge iframe found in round %d; checking anchor", total_rounds)
                    if self._verify_anchor_checked(timeout=4):
                        self.logger.info("Anchor verified checked; solve successful")
                        self._create_success_gif(screenshot_paths)
                        return True
                    else:
                        self.logger.warning("No challenge but anchor not checked; continuing")
                    time.sleep(1.5)
                    continue

                # Capture challenge state
                try:
                    target_element = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.ID, "rc-imageselect-target"))
                    )
                    challenge_path = os.path.join(
                        self.screenshot_dir, f"challenge_target_round_{total_rounds}.png"
                    )
                    target_element.screenshot(challenge_path)
                    screenshot_paths.append(challenge_path)
                    challenge_llm_path = self._prepare_image_for_llm(
                        challenge_path,
                        suffix=f"challenge_round_{total_rounds}",
                    )
                except TimeoutException:
                    self.logger.debug("Challenge target not found in round %d; skipping", total_rounds)
                    self.driver.switch_to.default_content()
                    continue

                # Get instructions
                try:
                    instruction_element = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "rc-imageselect-instructions"))
                    )
                    instruction_text = instruction_element.text.strip()
                    self.logger.debug("Round %d instruction text: %s", total_rounds, instruction_text)

                    object_name = self._parse_instruction_text(instruction_text)
                    if not object_name:
                        instruction_path = os.path.join(
                            self.screenshot_dir, f"instruction_round_{total_rounds}.png"
                        )
                        instruction_element.screenshot(instruction_path)
                        screenshot_paths.append(instruction_path)
                        object_name = ask_recaptcha_instructions_to_gemini(instruction_path, self.model)
                        self.logger.info("Round %d target object (Gemini): %s", total_rounds, object_name)
                    else:
                        self.logger.info("Round %d target object (DOM): %s", total_rounds, object_name)
                except TimeoutException:
                    self.logger.warning("Instructions not found in round %d; skipping", total_rounds)
                    self.driver.switch_to.default_content()
                    continue

                if object_name == "skip":
                    self.logger.info("Round %d: skipping; reloading", total_rounds)
                    self._click_skip_button()
                    self.driver.switch_to.default_content()
                    time.sleep(1.5)
                    clicked_tile_indices.clear()
                    last_object_name = ""
                    last_click_count = 0
                    continue

                # Detect new task (object change or many prior clicks)
                is_new_object = object_name.lower() != last_object_name.lower()
                if is_new_object or last_click_count >= 3:
                    clicked_tile_indices.clear()
                    if is_new_object:
                        self.logger.debug("Round %d: new object '%s'; resetting clicked tiles", total_rounds, object_name)
                    else:
                        self.logger.debug("Round %d: same object but >=3 clicks last round; resetting", total_rounds)
                last_object_name = object_name

                # Collect tiles (handles 3x3, 4x4, single image, etc.)
                try:
                    table = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located(
                            (By.XPATH, "//table[contains(@class, 'rc-imageselect-table')]")
                        )
                    )
                    tiles = table.find_elements(By.TAG_NAME, "td")
                    if not tiles:
                        self.logger.warning("No tiles found in round %d; skipping", total_rounds)
                        self.driver.switch_to.default_content()
                        continue
                except TimeoutException:
                    self.logger.warning("Tile table not found in round %d; skipping", total_rounds)
                    self.driver.switch_to.default_content()
                    continue

                tile_llm_paths = []
                for i, tile in enumerate(tiles):
                    tile_path = os.path.join(self.screenshot_dir, f"tile_round_{total_rounds}_{i}.png")
                    tile.screenshot(tile_path)
                    screenshot_paths.append(tile_path)
                    tile_llm_paths.append(self._prepare_image_for_llm(tile_path, suffix=f"tile_round_{total_rounds}_{i}"))

                # Classify tiles in parallel
                selected_indices: Set[int] = set()
                max_workers = min(6, max(1, len(tiles)))
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    futures = {
                        executor.submit(
                            self._classify_tile,
                            total_rounds,
                            i,
                            tile_llm_paths[i],
                            object_name,
                            challenge_llm_path,
                        ): i
                        for i in range(len(tiles))
                    }
                    for future in as_completed(futures):
                        idx, response = future.result()
                        if response == "true":
                            selected_indices.add(idx)

                new_tiles = sorted(idx for idx in selected_indices if idx not in clicked_tile_indices)
                self.logger.info(
                    "Round %d: AI selected %s (new: %s)",
                    total_rounds,
                    sorted(selected_indices),
                    new_tiles,
                )
                last_click_count = len(new_tiles)

                # Click new tiles
                for idx in new_tiles:
                    try:
                        if tiles[idx].is_displayed() and tiles[idx].is_enabled():
                            tiles[idx].click()
                            time.sleep(random.uniform(0.2, 0.5))
                    except (StaleElementReferenceException, Exception) as exc:
                        self.logger.debug("Failed to click tile %d in round %d: %s", idx, total_rounds, exc)

                clicked_tile_indices.update(new_tiles)

                # Attempt to verify
                challenge_completed = False
                try:
                    verify_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.ID, "recaptcha-verify-button"))
                    )
                    verify_button.click()
                    time.sleep(random.uniform(1.0, 1.5))

                    # Check if button disabled or challenge closed
                    try:
                        if verify_button.get_attribute("disabled"):
                            self.logger.info("Verify button disabled in round %d; likely completed", total_rounds)
                            challenge_completed = True
                    except Exception:
                        self.logger.debug("Verify button state check failed; assuming completion")
                        challenge_completed = True
                except TimeoutException:
                    self.logger.debug("No verify button in round %d; challenge may auto-complete", total_rounds)
                    challenge_completed = True
                except Exception as exc:
                    self.logger.debug("Verify click failed in round %d: %s", total_rounds, exc)

                # Switch out and check if challenge persists
                self.driver.switch_to.default_content()
                time.sleep(2)  # Allow DOM update

                # If challenge gone, verify anchor
                if challenge_completed or not self._switch_to_challenge_iframe(timeout=2):
                    if self._verify_anchor_checked(timeout=4):
                        self.logger.info("Anchor checked after round %d; solve successful", total_rounds)
                        self._create_success_gif(screenshot_paths)
                        return True
                    else:
                        self.logger.debug("Anchor not checked yet; continuing if rounds remain")

            self.logger.warning("Max %d rounds reached without solving", max_rounds)
            self._create_success_gif(screenshot_paths, success=False)
            return False

        except Exception as e:
            self.logger.error("Unexpected error during reCAPTCHA solve: %s", e)
            self._create_success_gif(screenshot_paths, success=False)
            return False
        finally:
            self.driver.switch_to.default_content()

    def _click_recaptcha_checkbox(self):
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
            state_after = state
            for attempt in range(2):
                try:
                    self.driver.execute_script("arguments[0].click();", checkbox)
                except StaleElementReferenceException:
                    checkbox = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.ID, "recaptcha-anchor"))
                    )
                    self.driver.execute_script("arguments[0].click();", checkbox)
                time.sleep(random.uniform(0.6, 1.2))
                try:
                    state_after = checkbox.get_attribute("aria-checked")
                except StaleElementReferenceException:
                    checkbox = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.ID, "recaptcha-anchor"))
                    )
                    state_after = checkbox.get_attribute("aria-checked")
                if state_after == "true":
                    self.logger.info("Clicked reCAPTCHA checkbox via JS")
                    return True
                self.logger.debug(
                    "Checkbox click attempt %d left anchor state %s",
                    attempt + 1,
                    state_after,
                )
            self.driver.switch_to.default_content()
            if self._challenge_iframe_present(timeout=5):
                self.logger.info("Challenge iframe detected after checkbox click")
                return True
            self.logger.debug(
                "Checkbox state after click attempts remained %s", state_after
            )
            return False
        except TimeoutException:
            self.logger.debug("Anchor iframe not available for checkbox click")
            return False
        except Exception as exc:  # pylint: disable=broad-except
            self.logger.warning("Error clicking reCAPTCHA checkbox: %s", exc)
            return False
        finally:
            self.driver.switch_to.default_content()

    def _classify_tile(self, round_number, tile_index, image_path, object_name, context_path=None):
        try:
            response = ask_if_tile_contains_object_gemini(
                image_path,
                object_name,
                self.model,
                context_image_path=context_path,
            )
            self.logger.info(
                "Round %d tile %d Gemini classification: %s",
                round_number,
                tile_index,
                response,
            )
            return tile_index, response
        except Exception as exc:  # pylint: disable=broad-except
            self.logger.warning(
                "Round %d tile %d classification failed: %s",
                round_number,
                tile_index,
                exc,
            )
            return tile_index, None

    def _prepare_image_for_llm(self, image_path, suffix="processed"):
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

    def _switch_to_challenge_iframe(self, timeout=3):
        """Attempt to switch into the challenge iframe if it is present."""
        try:
            challenge_iframe = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//iframe[contains(@title, 'recaptcha challenge expires in two minutes')]",
                    )
                )
            )
            self.driver.switch_to.frame(challenge_iframe)
            self.logger.info("Switched to challenge iframe")
            return True
        except TimeoutException:
            self.logger.debug("Challenge iframe not found within %d seconds", timeout)
            return False

    def _challenge_iframe_present(self, timeout=3) -> bool:
        """Detect if the challenge iframe exists without switching into it."""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//iframe[contains(@title, 'recaptcha challenge')]")
                )
            )
            return True
        except TimeoutException:
            return False

    def _verify_anchor_checked(self, timeout=3) -> bool:
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

    def _parse_instruction_text(self, instruction_text):
        if not instruction_text:
            return None
        lower = instruction_text.lower()
        lower = lower.replace("\n", " ")
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

    def _click_skip_button(self):
        try:
            skip_button = WebDriverWait(self.driver, 3).until(
                EC.element_to_be_clickable((By.ID, "recaptcha-reload-button"))
            )
            skip_button.click()
        except Exception as exc:  # pylint: disable=broad-except
            self.logger.debug("Skip button click failed: %s", exc)

    def _take_screenshot(self, name):
        path = os.path.join(self.screenshot_dir, f"{name}.png")
        self.driver.save_screenshot(path)
        return path

    def _create_success_gif(self, image_paths, success=True):
        if not image_paths:
            return
        valid_images = [Image.open(p).convert("RGB") for p in image_paths if os.path.exists(p)]
        if not valid_images:
            return
        # Resize to max size
        max_w, max_h = max(img.width for img in valid_images), max(img.height for img in valid_images)
        processed = []
        for img in valid_images:
            canvas = Image.new('RGB', (max_w, max_h), (255, 255, 255))
            pos = ((max_w - img.width) // 2, (max_h - img.height) // 2)
            canvas.paste(img, pos)
            processed.append(canvas)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = os.path.join(self.success_dir, f"recaptcha_{'success' if success else 'fail'}_{timestamp}.gif")
        processed[0].save(output, save_all=True, append_images=processed[1:], duration=800, loop=0)
        if success:
            self.logger.info("Captured successful reCAPTCHA solve GIF at %s", output)
        else:
            self.logger.info("Captured failed reCAPTCHA solve GIF at %s", output)
