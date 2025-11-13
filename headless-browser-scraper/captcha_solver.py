import logging
import os
import random
import time
from datetime import datetime

from PIL import Image
import imageio
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
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

                # Click the checkbox inside the anchor iframe when present.
                try:
                    self.driver.switch_to.default_content()
                    WebDriverWait(self.driver, 5).until(
                        EC.frame_to_be_available_and_switch_to_it(
                            (
                                By.XPATH,
                                "//iframe[contains(@title, 'reCAPTCHA') and not(contains(@title, 'challenge'))]",
                            )
                        )
                    )
                    checkbox = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.ID, "recaptcha-anchor"))
                    )
                    checkbox.click()
                    self.logger.info("Clicked reCAPTCHA checkbox")
                    time.sleep(random.uniform(0.6, 1.2))
                except TimeoutException:
                    self.logger.debug(
                        "Anchor iframe not available during attempt %d", attempt + 1
                    )
                except Exception as exc:  # pylint: disable=broad-except
                    self.logger.warning(
                        "Attempt %d: error clicking reCAPTCHA checkbox: %s",
                        attempt + 1,
                        exc,
                    )
                finally:
                    self.driver.switch_to.default_content()

                # Check for challenge iframe
                try:
                    challenge_iframe = WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located(
                            (
                                By.XPATH,
                                "//iframe[contains(@src, 'recaptcha') and contains(@title, 'challenge')]",
                            )
                        )
                    )
                    self.driver.switch_to.frame(challenge_iframe)
                    self.logger.info("Challenge iframe detected")
                except TimeoutException:
                    self.logger.info(
                        "No image challenge presented during attempt %d; assuming success",
                        attempt + 1,
                    )
                    self.driver.switch_to.default_content()
                    self._create_success_gif(screenshot_paths)
                    return True

                # Handle image challenge
                instruction_element = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "rc-imageselect-instructions")))
                instruction_path = os.path.join(self.screenshot_dir, f"instruction_{attempt+1}.png")
                instruction_element.screenshot(instruction_path)
                screenshot_paths.append(instruction_path)

                object_name = ask_recaptcha_instructions_to_gemini(instruction_path, self.model)
                self.logger.info("Attempt %d target object: %s", attempt + 1, object_name)

                table = self.driver.find_element(By.XPATH, "//table[contains(@class, 'rc-imageselect-table')]")
                tiles = table.find_elements(By.TAG_NAME, "td")

                tile_paths = []
                for i, tile in enumerate(tiles):
                    tile_path = os.path.join(self.screenshot_dir, f"tile_{attempt+1}_{i}.png")
                    tile.screenshot(tile_path)
                    tile_paths.append(tile_path)
                    screenshot_paths.append(tile_path)

                # Use AI to identify tiles
                tiles_to_click = []
                for i, path in enumerate(tile_paths):
                    if ask_if_tile_contains_object_gemini(path, object_name, self.model) == 'true':
                        tiles_to_click.append(i)

                # Click tiles
                for i in tiles_to_click:
                    if tiles[i].is_displayed():
                        tiles[i].click()
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
