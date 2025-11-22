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

def ask_text_to_gemini(image_path, model=None):
    prompt = "Act as a blind person assistant. Read the text from the image and give me only the text answer."
    payload = [_image_part(image_path), prompt]
    return _model_text_response(payload, "ask_text_to_gemini", model)

def ask_recaptcha_instructions_to_gemini(image_path, model=None):
    prompt = (
        "Analyze the blue instruction bar in the image. Identify the primary object"
        " the user is asked to select. For example, if it says 'Select all squares"
        " with motorcycles', the object is 'motorcycles'. Respond with only the"
        " single object name in lowercase. If the instruction is to 'click skip',"
        " return 'skip'."
    )
    payload = [_image_part(image_path), prompt]
    return _model_text_response(payload, "ask_recaptcha_instructions_to_gemini", model).lower()

def ask_if_tile_contains_object_gemini(image_path, object_name, model=None, context_image_path=None):
    prompt = (
        f"Does this image clearly contain a '{object_name}' or a recognizable part of a '{object_name}'? "
        "Respond only with 'true' if you are certain. If you are unsure or cannot tell confidently, respond only with 'false'."
    )
    payload = []
    if context_image_path:
        payload.append(_image_part(context_image_path))
    payload.extend([_image_part(image_path), prompt])
    return _model_text_response(payload, f"ask_if_tile_contains_object_gemini:{object_name}", model).lower()
