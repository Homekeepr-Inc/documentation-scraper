import base64
import logging
import os
import re
import time
from functools import lru_cache
from typing import Any, Iterable, List, Optional

from dotenv import load_dotenv

try:  # Optional dependency; functions guard against missing client.
    from openai import APIStatusError, OpenAI  # type: ignore
except Exception:  # pylint: disable=broad-except
    OpenAI = None  # type: ignore
    APIStatusError = Exception  # type: ignore

try:  # Prefer the modern google-genai SDK used by the reference project.
    from google import genai  # type: ignore
    from google.genai import types as genai_types  # type: ignore
except Exception:  # pylint: disable=broad-except
    genai = None  # type: ignore
    genai_types = None  # type: ignore

load_dotenv()

logger = logging.getLogger("headless.ai_utils")

_DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------
def image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def _detect_image_mime_type(path: str) -> str:
    lower = path.lower()
    if lower.endswith(".png"):
        return "image/png"
    if lower.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    if lower.endswith(".webp"):
        return "image/webp"
    return "image/png"


def _detect_audio_mime_type(path: str) -> str:
    lower = path.lower()
    if lower.endswith(".mp3"):
        return "audio/mpeg"
    if lower.endswith(".wav"):
        return "audio/wav"
    if lower.endswith(".ogg"):
        return "audio/ogg"
    return "audio/mpeg"


def _ensure_gemini_dependencies() -> None:
    if genai is None or genai_types is None:
        raise RuntimeError(
            "google-genai package is not installed. Install it to enable Gemini helpers."
        )


@lru_cache(maxsize=1)
def _get_gemini_client() -> Any:
    _ensure_gemini_dependencies()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("Gemini API key not configured.")
    return genai.Client(api_key=api_key)


def _gemini_part_from_path(path: str, mime_type: Optional[str] = None) -> Any:
    _ensure_gemini_dependencies()
    resolved_mime = mime_type or _detect_image_mime_type(path)
    with open(path, "rb") as file:
        data = file.read()
    return genai_types.Part.from_bytes(data=data, mime_type=resolved_mime)


def _gemini_audio_part(path: str) -> Any:
    _ensure_gemini_dependencies()
    mime_type = _detect_audio_mime_type(path)
    with open(path, "rb") as file:
        data = file.read()
    return genai_types.Part.from_bytes(data=data, mime_type=mime_type)


def _summarize_genai_response(response: Any) -> str:
    try:
        return str(response.to_dict())
    except Exception:  # pylint: disable=broad-except
        return repr(response)


def _gemini_generate(
    contents: Iterable[Any],
    context: str,
    model: Optional[str] = None,
    system_instruction: Optional[str] = None,
) -> str:
    client = _get_gemini_client()
    model_name = model or _DEFAULT_GEMINI_MODEL
    payload = list(contents)

    try:
        kwargs: dict[str, Any] = {}
        if system_instruction:
            config = None
            if genai_types is not None and hasattr(genai_types, "GenerateContentConfig"):
                try:
                    config = genai_types.GenerateContentConfig(
                        system_instruction=system_instruction
                    )
                except TypeError:
                    config = None
            kwargs["config"] = (
                config if config is not None else {"system_instruction": system_instruction}
            )

        response = client.models.generate_content(
            model=model_name,
            contents=payload,
            **kwargs,
        )
        text = (getattr(response, "text", "") or "").strip()
        logger.info("Gemini response (%s) for %s: %s", model_name, context, text)
        logger.debug(
            "Gemini raw response for %s: %s", context, _summarize_genai_response(response)
        )
        return text
    except Exception as exc:  # pylint: disable=broad-except
        logger.warning(
            "Gemini request failed for %s using model %s: %s", context, model_name, exc
        )
        raise


def _require_openai_client() -> OpenAI:
    if OpenAI is None:
        raise RuntimeError("openai package is not installed.")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OpenAI API key not configured.")
    return OpenAI(api_key=api_key)


# ---------------------------------------------------------------------------
# Gemini helpers
# ---------------------------------------------------------------------------
def ask_text_to_gemini(image_path: str, model: Optional[str] = None) -> str:
    prompt = (
        "Act as a blind person assistant. Read the text from the image and give only the text answer. "
        "If there is no text, reply with an empty string."
    )
    contents = [_gemini_part_from_path(image_path), prompt]
    return _gemini_generate(contents, "ask_text_to_gemini", model)


def ask_recaptcha_instructions_to_gemini(
    image_path: str, model: Optional[str] = None
) -> str:
    prompt = (
        "Analyze the blue instruction bar in the image. Identify the primary object the user is asked to select. "
        "Respond with only the single object name in lowercase. If the instruction is to 'click skip', return 'skip'."
    )
    contents = [_gemini_part_from_path(image_path), prompt]
    return _gemini_generate(
        contents, "ask_recaptcha_instructions_to_gemini", model
    ).lower()


def ask_if_tile_contains_object_gemini(
    image_path: str,
    object_name: str,
    model: Optional[str] = None,
    context_image_path: Optional[str] = None,
) -> str:
    prompt = (
        f"Does this image clearly contain a '{object_name}' or a recognizable part of it? "
        "Respond only with 'true' if you are certain. If unsure, respond only with 'false'."
    )
    contents: List[Any] = [_gemini_part_from_path(image_path)]
    if context_image_path:
        contents.append(_gemini_part_from_path(context_image_path))
    contents.append(prompt)
    return _gemini_generate(
        contents, f"ask_if_tile_contains_object_gemini:{object_name}", model
    ).lower()


def ask_puzzle_distance_to_gemini(image_path: str, model: Optional[str] = None) -> str:
    prompt = (
        "Analyze the image and determine the correct slider movement needed to solve the puzzle CAPTCHA.\n"
        "* Drag the slider so the center line of the white handle aligns exactly with the horizontal center of the empty slot.\n"
        "* Report the horizontal pixel distance from the current handle center to the slot center.\n"
        "* Movement is horizontal only, to the right, capped at 260.\n"
        "* If already aligned, return 0.\n"
        "Respond only with the integer value."
    )
    contents = [_gemini_part_from_path(image_path), prompt]
    return _gemini_generate(contents, "ask_puzzle_distance_to_gemini", model)


def ask_puzzle_correction_to_gemini(image_path: str, model: Optional[str] = None) -> str:
    prompt = (
        "**CRITICAL ALIGNMENT CORRECTION.** Determine the final pixel adjustment required to perfectly align the "
        "puzzle piece into its slot. Respond with a positive integer to move right, a negative integer to move left, "
        "or 0 if already perfect. Return only the integer."
    )
    contents = [_gemini_part_from_path(image_path), prompt]
    return _gemini_generate(contents, "ask_puzzle_correction_to_gemini", model)


def ask_puzzle_correction_direction_to_gemini(
    image_path: str, model: Optional[str] = None
) -> str:
    prompt = (
        "If the puzzle piece is to the left of the target slot, respond only with '+'. "
        "If it is to the right, respond only with '-'."
    )
    contents = [_gemini_part_from_path(image_path), prompt]
    return _gemini_generate(
        contents, "ask_puzzle_correction_direction_to_gemini", model
    ).strip()


def ask_best_fit_to_gemini(
    image_paths: Iterable[str], model: Optional[str] = None
) -> str:
    prompt = (
        "You are given multiple images of a slider puzzle attempt. Choose the image where the puzzle piece "
        "fits the slot with no visible gaps. Respond only with the index number (0-based) of the best image."
    )
    contents: List[Any] = [prompt]
    for path in image_paths:
        contents.append(_gemini_part_from_path(path))
    return _gemini_generate(contents, "ask_best_fit_to_gemini", model)


def ask_audio_to_gemini(audio_path: str, model: Optional[str] = None) -> str:
    system_instruction = (
        "The audio is in American English. Type only the letters you hear clearly and loudly spoken. "
        "Ignore any background words, sounds, or faint speech. Enter the letters in the exact order they are spoken."
    )
    contents = ["Transcribe the captcha from the audio file.", _gemini_audio_part(audio_path)]
    transcription = _gemini_generate(
        contents,
        "ask_audio_to_gemini",
        model=model,
        system_instruction=system_instruction,
    )
    return re.sub(r"[^a-zA-Z0-9]", "", transcription)


# ---------------------------------------------------------------------------
# OpenAI helpers (optional)
# ---------------------------------------------------------------------------
def ask_text_to_chatgpt(image_path: str, model: Optional[str] = None) -> str:
    client = _require_openai_client()
    base64_image = image_to_base64(image_path)
    system_prompt = (
        "Act as a blind person assistant. Read the text from the image and give only the text answer."
    )
    model_to_use = model or "gpt-4o"
    response = client.chat.completions.create(
        model=model_to_use,
        messages=[
            {"role": "system", "content": [{"type": "text", "text": system_prompt}]},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                    },
                    {
                        "type": "text",
                        "text": "Give only the text from the image. If none, return an empty string.",
                    },
                ],
            },
        ],
        temperature=1,
        max_tokens=256,
    )
    return response.choices[0].message.content.strip()


def ask_puzzle_distance_to_chatgpt(
    image_path: str, model: Optional[str] = None
) -> Optional[str]:
    client = _require_openai_client()
    base64_image = image_to_base64(image_path)
    prompt = (
        "As an assistant designed to help a visually impaired individual, determine the horizontal pixel distance "
        "needed to move the slider handle so its center aligns with the center of the empty slot. Movement is "
        "horizontal only, always to the right, and capped at 260. Return a single non-negative integer. "
        "If already aligned, return 0."
    )
    model_to_use = model or "gpt-4o"
    response = client.chat.completions.create(
        model=model_to_use,
        messages=[
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                    }
                ],
            },
        ],
        temperature=0,
        max_tokens=50,
    )
    content = response.choices[0].message.content.strip()
    match = re.search(r"-?\d+", content)
    if match:
        return match.group(0)
    logger.warning(
        "OpenAI distance response did not contain an integer: '%s'.", content
    )
    return None


def ask_puzzle_correction_to_chatgpt(
    image_path: str, model: Optional[str] = None
) -> str:
    client = _require_openai_client()
    base64_image = image_to_base64(image_path)
    prompt = (
        "**CRITICAL ALIGNMENT CORRECTION.** Determine the final pixel adjustment required to perfectly align the "
        "puzzle piece into its slot. Respond with a positive integer to move right, a negative integer to move left, "
        "or 0 if already perfect. Output only the integer."
    )
    model_to_use = model or "gpt-4o"
    response = client.chat.completions.create(
        model=model_to_use,
        messages=[
            {
                "role": "system",
                "content": prompt,
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                    }
                ],
            },
        ],
        temperature=0,
        max_tokens=20,
    )
    return response.choices[0].message.content.strip()


def ask_puzzle_correction_direction_to_openai(
    image_path: str, model: Optional[str] = None
) -> str:
    client = _require_openai_client()
    base64_image = image_to_base64(image_path)
    prompt = (
        "You are an expert in slider puzzles. If the puzzle piece is to the LEFT of the slot respond only with '+'. "
        "If it is to the RIGHT respond only with '-'."
    )
    model_to_use = model or "gpt-4o"
    response = client.chat.completions.create(
        model=model_to_use,
        messages=[
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                    }
                ],
            },
        ],
        temperature=0,
        max_tokens=5,
    )
    return response.choices[0].message.content.strip()


def ask_best_fit_to_openai(
    image_paths: Iterable[str], model: Optional[str] = None
) -> Optional[str]:
    client = _require_openai_client()
    prompt = (
        "You are given multiple images of a puzzle CAPTCHA attempt. Select the image where the puzzle piece is placed "
        "most correctly into the slot. There must be no visible gap. Respond only with the index number (0-based)."
    )
    user_content = [{"type": "text", "text": prompt}]
    for path in image_paths:
        user_content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{image_to_base64(path)}"},
            }
        )

    model_to_use = model or "gpt-4o"
    response = client.chat.completions.create(
        model=model_to_use,
        messages=[
            {"role": "system", "content": "You are an expert at analyzing puzzle captcha images."},
            {"role": "user", "content": user_content},
        ],
        temperature=0,
        max_tokens=10,
    )
    content = response.choices[0].message.content.strip()
    match = re.search(r"\d+", content)
    if match:
        return match.group(0)
    logger.warning("OpenAI best-fit response did not contain an integer: '%s'.", content)
    return None


def ask_audio_to_openai(audio_path: str, model: Optional[str] = None) -> str:
    client = _require_openai_client()
    prompt = "What is the captcha answer?"
    model_to_use = model or "gpt-4o-transcribe"
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with open(audio_path, "rb") as audio_file:
                response = client.audio.transcriptions.create(
                    model=model_to_use,
                    file=audio_file,
                    prompt=prompt,
                )
            return re.sub(r"[^a-zA-Z0-9]", "", response.text.strip())
        except APIStatusError as err:  # type: ignore[attr-defined]
            if getattr(err, "status_code", None) == 503 and attempt < max_retries - 1:
                wait_time = 3 * (attempt + 1)
                logger.warning(
                    "OpenAI audio API overloaded (503). Retrying in %s seconds...", wait_time
                )
                time.sleep(wait_time)
                continue
            raise
        except Exception:  # pylint: disable=broad-except
            raise
    raise RuntimeError("Failed to transcribe audio with OpenAI after multiple retries.")


def ask_recaptcha_instructions_to_chatgpt(
    image_path: str, model: Optional[str] = None
) -> str:
    client = _require_openai_client()
    base64_image = image_to_base64(image_path)
    prompt = (
        "Analyze the blue instruction bar in the image. Identify the primary object the user is asked to select. "
        "Respond with only the single object name in lowercase. If the instruction is to 'click skip', return 'skip'."
    )
    model_to_use = model or "gpt-4o"
    response = client.chat.completions.create(
        model=model_to_use,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                    },
                ],
            }
        ],
        temperature=0,
        max_tokens=50,
    )
    return response.choices[0].message.content.strip().lower()


def ask_if_tile_contains_object_chatgpt(
    image_path: str, object_name: str, model: Optional[str] = None
) -> str:
    client = _require_openai_client()
    base64_image = image_to_base64(image_path)
    prompt = (
        f"Does this image clearly contain a '{object_name}' or a recognizable part of a '{object_name}'? "
        "Respond only with 'true' if you are certain. If unsure, respond only with 'false'."
    )
    model_to_use = model or "gpt-4o"
    response = client.chat.completions.create(
        model=model_to_use,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                    },
                ],
            }
        ],
        temperature=0,
        max_tokens=10,
    )
    return response.choices[0].message.content.strip().lower()
