import hashlib
import logging
import os
import random
import re
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FuturesTimeoutError
from typing import Any, Optional, Set, List, Dict

from PIL import Image
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
    MoveTargetOutOfBoundsException,
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from ai_utils import (
    ask_recaptcha_instructions_to_gemini,
    ask_if_tile_contains_object_gemini,
    ask_text_to_gemini
)


class CaptchaSolver:
    MAX_CLASSIFICATION_WORKERS = 6
    LLM_DECISION_TIMEOUT = 25

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
        clicked_tile_records: Dict[int, Dict[str, Any]] = {}
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
                    clicked_tile_records.clear()
                    last_object_name = ""
                    last_click_count = 0
                    continue

                # Detect new task (object change or many prior clicks)
                is_new_object = object_name.lower() != last_object_name.lower()
                if is_new_object or last_click_count >= 3:
                    clicked_tile_records.clear()
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

                tile_snapshots = self._capture_tile_snapshots(
                    tiles,
                    total_rounds,
                    snapshot_iteration=0,
                    screenshot_paths=screenshot_paths,
                )
                snapshot_iteration = 0
                classification_pass = 0
                newly_clicked_total: List[int] = []
                while True:
                    classification_pass += 1
                    indices_to_classify: List[int] = []
                    for idx, snapshot in tile_snapshots.items():
                        if snapshot["mode"] not in {"plain", "checkbox"}:
                            continue
                        record = clicked_tile_records.get(idx)
                        if (
                            record
                            and record.get("digest") == snapshot["digest"]
                            and record.get("mode") == snapshot["mode"]
                        ):
                            continue
                        indices_to_classify.append(idx)
                    if not indices_to_classify:
                        self.logger.debug(
                            "Round %d: no tiles left to classify in pass %d",
                            total_rounds,
                            classification_pass,
                        )
                        last_click_count = 0
                        break

                selected_indices: Set[int] = set()
                newly_clicked: List[int] = []
                max_workers = min(self.MAX_CLASSIFICATION_WORKERS, len(indices_to_classify))
                self.logger.info(
                    "Round %d pass %d: classifying %d tile(s) with %d worker(s)",
                    total_rounds,
                    classification_pass,
                    len(indices_to_classify),
                    max_workers,
                )
                with ThreadPoolExecutor(max_workers=max_workers or 1) as executor:
                    futures = {
                        executor.submit(
                            self._classify_tile,
                            total_rounds,
                            idx,
                            tile_snapshots[idx]["llm_path"],
                            object_name,
                            challenge_llm_path,
                        ): idx
                        for idx in indices_to_classify
                    }
                    for future in as_completed(futures):
                        idx = futures[future]
                        try:
                            result_idx, response = future.result(timeout=self.LLM_DECISION_TIMEOUT)
                        except FuturesTimeoutError:
                            self.logger.warning(
                                "Round %d tile %d classification timed out after %ds; retrying synchronously",
                                total_rounds,
                                idx,
                                self.LLM_DECISION_TIMEOUT,
                            )
                            future.cancel()
                            result_idx, response = self._classify_tile(
                                total_rounds,
                                idx,
                                tile_snapshots[idx]["llm_path"],
                                object_name,
                                challenge_llm_path,
                            )
                        if response == "true":
                            selected_indices.add(result_idx)
                            current_digest = tile_snapshots[result_idx]["digest"]
                            record = clicked_tile_records.get(result_idx)
                            if record and record.get("digest") == current_digest:
                                continue
                            new_mode = self._click_tile_immediately(
                                tiles, result_idx, total_rounds, tile_snapshots[result_idx]
                            )
                            if new_mode:
                                clicked_tile_records[result_idx] = {
                                    "digest": current_digest,
                                    "mode": new_mode,
                                }
                                newly_clicked.append(result_idx)
                            else:
                                self.logger.debug(
                                    "Round %d: tile %d marked positive but click skipped",
                                    total_rounds,
                                    result_idx,
                                )
                        elif response is None:
                            self.logger.debug(
                                "Round %d tile %d classification returned no decision",
                                total_rounds,
                                idx,
                            )

                self.logger.info(
                    "Round %d pass %d: AI marked tiles %s for clicking",
                    total_rounds,
                    classification_pass,
                    sorted(selected_indices),
                )
                if not selected_indices:
                    last_click_count = 0
                    break

                if not newly_clicked:
                    self.logger.debug(
                        "Round %d pass %d: all positive tiles already clicked",
                        total_rounds,
                        classification_pass,
                    )
                    last_click_count = 0
                    break

                newly_clicked_total.extend(newly_clicked)
                last_click_count = len(newly_clicked)

                if not self._wait_for_tile_refresh(
                    tiles,
                    total_rounds,
                    newly_clicked,
                    tile_snapshots,
                ):
                    self.logger.debug(
                        "Round %d pass %d: no tile refresh detected after clicks",
                        total_rounds,
                        classification_pass,
                    )
                    break

                snapshot_iteration += 1
                tile_snapshots = self._capture_tile_snapshots(
                    tiles,
                    total_rounds,
                    snapshot_iteration=snapshot_iteration,
                    screenshot_paths=screenshot_paths,
                )
                self._reset_clicked_records_if_tiles_changed(
                    clicked_tile_records,
                    tile_snapshots,
                )

                self.logger.info(
                    "Round %d: AI clicked tiles %s during challenge",
                    total_rounds,
                    sorted(set(newly_clicked_total)),
                )

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

    def _click_tile_immediately(
        self,
        tiles: List,
        idx: int,
        round_number: int,
        snapshot: Dict[str, Any],
    ) -> Optional[str]:
        """Click a tile when classification comes back positive.

        Returns the tile's mode after the click when a click occurs, otherwise None.
        """
        try:
            tile = tiles[idx]
            if snapshot.get("mode") == "tileselected":
                self.logger.debug("Round %d: tile %d already selected; skipping", round_number, idx)
                return None
            self._scroll_into_view(tile)
            click_targets = []
            if snapshot.get("has_checkbox"):
                try:
                    click_targets.append(
                        ("checkbox", tile.find_element(By.CLASS_NAME, "rc-imageselect-checkbox"))
                    )
                except NoSuchElementException:
                    self.logger.debug(
                        "Round %d: tile %d checkbox not located; falling back to non-checkbox targets",
                        round_number,
                        idx,
                    )
            click_targets.append(("tile", tile))
            for cls_name in ("rc-image-tile-target", "rc-image-tile-wrapper"):
                try:
                    click_targets.append((cls_name, tile.find_element(By.CLASS_NAME, cls_name)))
                except NoSuchElementException:
                    continue

            tried_labels = []
            for label, candidate in click_targets:
                tried_labels.append(label)
                if not candidate.is_displayed():
                    continue
                strategy = self._click_with_fallbacks(candidate)
                if not strategy and candidate is not tile:
                    strategy = self._click_with_fallbacks(tile)
                if strategy:
                    self.logger.info(
                        "Round %d: clicked tile %d (%s mode via %s on %s)",
                        round_number,
                        idx,
                        snapshot.get("mode"),
                        strategy,
                        label,
                    )
                    time.sleep(random.uniform(0.2, 0.5))
                    updated_mode = self._derive_tile_mode(
                        tile.get_attribute("class") or "",
                        self._tile_has_checkbox(tile),
                    )
                    return updated_mode
            self.logger.debug(
                "Round %d: tile %d could not be clicked; attempted targets=%s",
                round_number,
                idx,
                tried_labels,
            )
            return None
        except (StaleElementReferenceException, Exception) as exc:
            self.logger.debug("Round %d: failed to click tile %d: %s", round_number, idx, exc)
            return None

    def _click_with_fallbacks(self, element) -> Optional[str]:
        """Try multiple click strategies; return the strategy name on success."""
        strategies = (
            ("native", lambda el: el.click()),
            (
                "action_chains",
                lambda el: ActionChains(self.driver)
                .move_to_element(el)
                .pause(random.uniform(0.05, 0.15))
                .click()
                .perform(),
            ),
            ("javascript", lambda el: self.driver.execute_script("arguments[0].click();", el)),
        )
        for name, action in strategies:
            try:
                action(element)
                return name
            except (
                ElementClickInterceptedException,
                ElementNotInteractableException,
                MoveTargetOutOfBoundsException,
                StaleElementReferenceException,
            ) as exc:
                self.logger.debug("Click strategy %s failed: %s", name, exc)
            except Exception as exc:  # pylint: disable=broad-except
                self.logger.debug("Click strategy %s raised %s", name, exc)
        return None

    def _scroll_into_view(self, element):
        try:
            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center', inline: 'center'});", element
            )
            time.sleep(random.uniform(0.05, 0.1))
        except Exception:  # pylint: disable=broad-except
            pass

    def _capture_tile_snapshots(
        self,
        tiles: List,
        round_number: int,
        snapshot_iteration: int,
        screenshot_paths: List[str],
    ) -> Dict[int, Dict[str, Any]]:
        """Screenshot tiles and record hashes so we can detect fade-in replacements."""
        snapshots: Dict[int, Dict[str, Any]] = {}
        for idx, tile in enumerate(tiles):
            base_name = f"tile_round_{round_number}_{snapshot_iteration}_{idx}"
            tile_path = os.path.join(self.screenshot_dir, f"{base_name}.png")
            tile.screenshot(tile_path)
            screenshot_paths.append(tile_path)
            llm_path = self._prepare_image_for_llm(tile_path, suffix=base_name)
            digest = self._hash_file(tile_path)
            class_attr = tile.get_attribute("class") or ""
            has_checkbox = False
            try:
                tile.find_element(By.CLASS_NAME, "rc-imageselect-checkbox")
                has_checkbox = True
            except NoSuchElementException:
                has_checkbox = False
            mode = self._derive_tile_mode(class_attr, has_checkbox)
            snapshots[idx] = {
                "raw_path": tile_path,
                "llm_path": llm_path,
                "digest": digest,
                "class": class_attr,
                "has_checkbox": has_checkbox,
                "mode": mode,
            }
        return snapshots

    def _derive_tile_mode(self, class_attr: str, has_checkbox: bool) -> str:
        lowered = class_attr.lower()
        if "rc-imageselect-dynamic-selected" in lowered:
            return "dynamic-selected"
        if "rc-imageselect-tileselected" in lowered:
            return "tileselected"
        if has_checkbox:
            return "checkbox"
        return "plain"

    def _tile_has_checkbox(self, tile) -> bool:
        try:
            tile.find_element(By.CLASS_NAME, "rc-imageselect-checkbox")
            return True
        except (NoSuchElementException, StaleElementReferenceException):
            return False

    def _hash_file(self, file_path: str) -> str:
        try:
            with open(file_path, "rb") as file_handle:
                return hashlib.md5(file_handle.read()).hexdigest()
        except Exception as exc:  # pylint: disable=broad-except
            self.logger.debug("Unable to hash file %s: %s", file_path, exc)
            return ""

    def _wait_for_tile_refresh(
        self,
        tiles: List,
        round_number: int,
        clicked_indices: List[int],
        previous_snapshots: Dict[int, Dict[str, Any]],
        max_wait: float = 6.0,
    ) -> bool:
        """Wait for any of the clicked tiles to refresh with new imagery."""
        if not clicked_indices:
            return False
        baseline = {
            idx: {
                "digest": previous_snapshots.get(idx, {}).get("digest"),
                "mode": previous_snapshots.get(idx, {}).get("mode"),
            }
            for idx in clicked_indices
        }
        start_time = time.time()
        while time.time() - start_time < max_wait:
            time.sleep(0.55)
            changed = []
            for idx in clicked_indices:
                original = baseline.get(idx)
                if not original:
                    continue
                try:
                    png_bytes = tiles[idx].screenshot_as_png
                    class_attr = tiles[idx].get_attribute("class") or ""
                except Exception as exc:  # pylint: disable=broad-except
                    self.logger.debug(
                        "Round %d: unable to rescreenshot tile %d during refresh detection: %s",
                        round_number,
                        idx,
                        exc,
                    )
                    continue
                new_digest = hashlib.md5(png_bytes).hexdigest()
                new_mode = self._derive_tile_mode(
                    class_attr,
                    self._tile_has_checkbox(tiles[idx]),
                )
                if new_digest != original["digest"] or new_mode != original["mode"]:
                    changed.append(idx)
            if changed:
                self.logger.info(
                    "Round %d: detected refreshed tiles %s",
                    round_number,
                    changed,
                )
                return True
        return False

    def _reset_clicked_records_if_tiles_changed(
        self,
        clicked_records: Dict[int, Dict[str, Any]],
        tile_snapshots: Dict[int, Dict[str, Any]],
    ):
        """Drop clicked records for tiles whose content changed so they can be reclassified."""
        stale_indices = [
            idx
            for idx, record in clicked_records.items()
            if (
                tile_snapshots.get(idx, {}).get("digest") != record.get("digest")
                or tile_snapshots.get(idx, {}).get("mode") != record.get("mode")
            )
        ]
        for idx in stale_indices:
            clicked_records.pop(idx, None)

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
