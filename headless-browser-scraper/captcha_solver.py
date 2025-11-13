import logging
import os
import random
import re
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from PIL import Image
import imageio
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

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

    def solve_recaptcha_v2(self, max_retries=3):
        screenshot_paths = []
        for attempt in range(max_retries):
            try:
                self.logger.info(
                    "reCAPTCHA v2 solve attempt %d/%d", attempt + 1, max_retries
                )

                # Ensure we're in default content at the start of each loop.
                self.driver.switch_to.default_content()

                checkbox_checked = self._click_recaptcha_checkbox()
                challenge_attached = self._switch_to_challenge_iframe(timeout=5)

                if not challenge_attached:
                    if checkbox_checked:
                        self.logger.info(
                            "No image challenge presented during attempt %d; assuming success",
                            attempt + 1,
                        )
                        self.driver.switch_to.default_content()
                        self._create_success_gif(screenshot_paths)
                        return True

                    self.logger.warning(
                        "Attempt %d: checkbox click did not register and no challenge displayed; retrying",
                        attempt + 1,
                    )
                    time.sleep(1.5)
                    self.logger.info(
                        "Re-checking for challenge iframe after delay (attempt %d)",
                        attempt + 1,
                    )
                    self.driver.switch_to.default_content()
                    challenge_attached = self._switch_to_challenge_iframe(timeout=3)
                    if not challenge_attached:
                        time.sleep(1.5)
                        continue

                # Handle image challenge
                target_element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "rc-imageselect-target"))
                )
                challenge_path = os.path.join(
                    self.screenshot_dir, f"challenge_target_{attempt+1}.png"
                )
                target_element.screenshot(challenge_path)
                screenshot_paths.append(challenge_path)
                challenge_llm_path = self._prepare_image_for_llm(
                    challenge_path,
                    suffix="challenge",
                )

                instruction_element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(
                        (By.CLASS_NAME, "rc-imageselect-instructions")
                    )
                )
                instruction_text = instruction_element.text.strip()
                self.logger.debug(
                    "Attempt %d instruction text: %s", attempt + 1, instruction_text
                )

                object_name = self._parse_instruction_text(instruction_text)
                if object_name:
                    self.logger.info(
                        "Attempt %d target object (parsed DOM): %s",
                        attempt + 1,
                        object_name,
                    )
                else:
                    instruction_path = os.path.join(
                        self.screenshot_dir, f"instruction_{attempt+1}.png"
                    )
                    instruction_element.screenshot(instruction_path)
                    screenshot_paths.append(instruction_path)
                    try:
                        object_name = ask_recaptcha_instructions_to_gemini(
                            instruction_path, self.model
                        )
                        self.logger.info(
                            "Attempt %d target object (Gemini): %s",
                            attempt + 1,
                            object_name,
                        )
                    except Exception as exc:  # pylint: disable=broad-except
                        self.logger.warning(
                            "Attempt %d failed extracting instructions via Gemini: %s",
                            attempt + 1,
                            exc,
                        )
                        raise

                if object_name == "skip":
                    self.logger.info(
                        "Attempt %d instruction requested skip; clicking skip button",
                        attempt + 1,
                    )
                    self._click_skip_button()
                    self.driver.switch_to.default_content()
                    time.sleep(1.5)
                    continue

                table = self.driver.find_element(By.XPATH, "//table[contains(@class, 'rc-imageselect-table')]")
                tiles = table.find_elements(By.TAG_NAME, "td")

                tile_paths = []
                tile_llm_paths = []
                for i, tile in enumerate(tiles):
                    tile_path = os.path.join(self.screenshot_dir, f"tile_{attempt+1}_{i}.png")
                    tile.screenshot(tile_path)
                    tile_paths.append(tile_path)
                    screenshot_paths.append(tile_path)
                    tile_llm_paths.append(
                        self._prepare_image_for_llm(tile_path, suffix=f"tile_{i}")
                    )

                # Use AI to identify tiles
                max_workers = min(6, max(1, len(tile_paths)))
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    futures = {
                        executor.submit(
                            self._classify_tile,
                            attempt + 1,
                            i,
                            tile_llm_paths[i],
                            object_name,
                            challenge_llm_path,
                        ): i
                        for i in range(len(tile_paths))
                    }
                    for future in as_completed(futures):
                        idx, response = future.result()
                        if response == 'true' and tiles[idx].is_displayed():
                            tiles[idx].click()
                            time.sleep(random.uniform(0.2, 0.5))

                # Verify and submit
                try:
                    verify_button = WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.ID, "recaptcha-verify-button")))
                    verify_button.click()
                    time.sleep(1.5)

                    if verify_button.get_attribute("disabled"):
                        self.logger.info("Challenge passed on attempt %d", attempt + 1)
                        self.driver.switch_to.default_content()
                        self._create_success_gif(screenshot_paths)
                        return True
                except Exception as exc:  # pylint: disable=broad-except
                    self.logger.debug(
                        "Attempt %d verify phase encountered exception: %s",
                        attempt + 1,
                        exc,
                    )

                self.driver.switch_to.default_content()
                time.sleep(2)

            except Exception as e:
                self.logger.warning("Attempt %d failed with exception: %s", attempt + 1, e)
                continue

        self.logger.error("All %d attempts to solve reCAPTCHA failed", max_retries)
        self._create_success_gif(screenshot_paths, success=False)
        return False

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
            self.driver.execute_script("arguments[0].click();", checkbox)
            time.sleep(random.uniform(0.6, 1.2))
            state_after = checkbox.get_attribute("aria-checked")
            if state_after == "true":
                self.logger.info("Clicked reCAPTCHA checkbox via JS")
                return True
            self.logger.debug(
                "Checkbox state after click attempt remained %s", state_after
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

    def _classify_tile(self, attempt_number, tile_index, image_path, object_name, context_path=None):
        try:
            response = ask_if_tile_contains_object_gemini(
                image_path,
                object_name,
                self.model,
                context_image_path=context_path,
            )
            self.logger.info(
                "Attempt %d tile %d Gemini classification: %s",
                attempt_number,
                tile_index,
                response,
            )
            return tile_index, response
        except Exception as exc:  # pylint: disable=broad-except
            self.logger.warning(
                "Attempt %d tile %d classification failed: %s",
                attempt_number,
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
                        "//iframe[contains(@src, 'recaptcha') and contains(@title, 'challenge')]",
                    )
                )
            )
            self.driver.switch_to.frame(challenge_iframe)
            self.logger.info("Challenge iframe detected")
            return True
        except TimeoutException:
            return False

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
