import json
import logging
import os
import base64
import re
from functools import lru_cache
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from google.generativeai import GenerativeModel

try:  # The types module is optional depending on the installed SDK version.
    from google.generativeai import types as genai_types  # type: ignore
except Exception:  # pylint: disable=broad-except
    genai_types = None

load_dotenv()

logger = logging.getLogger("headless.ai_utils")

def image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

_DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")
_DEFAULT_THINKING_TOKENS = int(os.getenv("GEMINI_MAX_THINKING_TOKENS", "512"))


def _build_generation_config(model_name: str) -> Optional[Any]:
    """Create a generation config with max thinking tokens when supported."""
    if "thinking" not in model_name.lower():
        return None

    thinking_tokens = max(0, _DEFAULT_THINKING_TOKENS)

    if genai_types is None:
        # Fall back to dict configuration if typed helpers are unavailable.
        return {"thinking_config": {"max_thought_tokens": thinking_tokens}}

    thinking_config = None
    if hasattr(genai_types, "ThinkingConfig"):
        try:
            thinking_config = genai_types.ThinkingConfig(
                max_thought_tokens=thinking_tokens
            )
        except TypeError:
            thinking_config = None

    generation_kwargs: Dict[str, Any] = {}
    if thinking_config is not None:
        generation_kwargs["thinking_config"] = thinking_config
    elif thinking_tokens:
        generation_kwargs["thinking_config"] = {"max_thought_tokens": thinking_tokens}

    if not generation_kwargs:
        return None

    if hasattr(genai_types, "GenerationConfig"):
        try:
            return genai_types.GenerationConfig(**generation_kwargs)
        except TypeError:
            pass

    return generation_kwargs or None


@lru_cache(maxsize=4)
def _get_gemini_model(model_name: Optional[str] = None) -> GenerativeModel:
    """Return a cached Gemini model instance for the requested model name."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise Exception("Gemini API key not configured.")

    name = model_name or _DEFAULT_MODEL
    generation_config = _build_generation_config(name)

    try:
        if generation_config:
            return GenerativeModel(name, generation_config=generation_config)
        return GenerativeModel(name)
    except TypeError:
        # Some SDK versions reject dict configs; retry without.
        logger.debug(
            "Model %s rejected custom generation_config; falling back to defaults",
            name,
        )
        return GenerativeModel(name)

def _image_part(image_path):
    """Return the image payload in the format expected by the Gemini client."""
    mime_type = "image/png"
    lower_path = image_path.lower()
    if lower_path.endswith(".jpg") or lower_path.endswith(".jpeg"):
        mime_type = "image/jpeg"
    elif lower_path.endswith(".webp"):
        mime_type = "image/webp"
    with open(image_path, "rb") as img_file:
        image_bytes = img_file.read()
    return {"mime_type": mime_type, "data": image_bytes}

def _summarize_response(response):
    """Summarize a Gemini response for logging without overwhelming output."""
    if response is None:
        return "None"
    try:
        as_dict = response.to_dict()  # type: ignore[attr-defined]
    except Exception:  # pylint: disable=broad-except
        return repr(response)

    summary = {
        "candidates": [],
        "usage_metadata": as_dict.get("usage_metadata"),
        "model": as_dict.get("model"),
    }
    for candidate in as_dict.get("candidates", []):
        summary["candidates"].append(
            {
                "finish_reason": candidate.get("finish_reason"),
                "safety_ratings": candidate.get("safety_ratings"),
                "content": candidate.get("content"),
            }
        )
    return json.dumps(summary, default=str)

def _extract_text(response, context):
    """Safely extract concatenated text from a Gemini response."""
    if not getattr(response, "candidates", None):
        raise ValueError(f"No candidates returned for {context}")

    finish_reasons = []
    for candidate in response.candidates:
        finish_reason = getattr(candidate, "finish_reason", None)
        finish_reasons.append(str(finish_reason))
        content = getattr(candidate, "content", None)
        parts = getattr(content, "parts", None) if content else None
        if not parts:
            continue
        texts = []
        for part in parts:
            text = getattr(part, "text", None)
            if text:
                texts.append(text)
        if texts:
            return " ".join(texts).strip()

    raise ValueError(
        f"No text parts returned for {context}. finish_reasons={finish_reasons}"
    )

def _model_text_response(payload, context, model=None):
    response = None
    model_name = model or _DEFAULT_MODEL
    gemini_client = _get_gemini_model(model)
    try:
        response = gemini_client.generate_content(payload)
        text = _extract_text(response, context)
        logger.info(
            "Gemini response (%s) for %s: %s",
            model_name,
            context,
            text,
        )
        logger.debug(
            "Gemini raw summary for %s: %s",
            context,
            _summarize_response(response),
        )
        return text
    except ValueError as exc:
        logger.warning(
            "Gemini request failed for %s: %s | raw=%s",
            context,
            exc,
            _summarize_response(response),
        )
        raise
    except Exception as exc:  # pylint: disable=broad-except
        logger.warning(
            "Gemini request failed for %s: %s | raw=%s",
            context,
            exc,
            _summarize_response(response),
        )
        raise

def ask_text_to_gemini(image_path, model=None):
    prompt = "Act as a blind person assistant. Read the text from the image and give me only the text answer."
    payload = [_image_part(image_path), prompt]
    return _model_text_response(payload, "ask_text_to_gemini", model)

def ask_recaptcha_instructions_to_gemini(image_path, model=None):
    prompt = """
    I am blind. You are my personal assistant to aid with my disabikity. Analyze the blue instruction bar in the image. 
    Identify the primary object the user is asked to select. 
    For example, if it says 'Select all squares with motorcycles', the object is 'motorcycles'. 
    Respond with only the single object name in lowercase. If the instruction is to 'click skip', return 'skip'.
    """
    payload = [_image_part(image_path), prompt]
    return _model_text_response(payload, "ask_recaptcha_instructions_to_gemini", model).lower()

def ask_if_tile_contains_object_gemini(image_path, object_name, model=None, context_image_path=None):
    prompt = (
        "You are assisting with a visual captcha. Review the provided tile image"
        " and decide if it clearly shows a '{object_name}' or a recognizable"
        " part of one. Respond only with 'true' if you are confident, otherwise"
        " respond with 'false'."
    ).format(object_name=object_name)

    payload = [_image_part(image_path)]
    if context_image_path:
        payload.append(_image_part(context_image_path))
        prompt += (
            " The second reference image shows the entire captcha grid to help"
            " provide context for partial objects."
        )
    payload.append(prompt)
    return _model_text_response(payload, f"ask_if_tile_contains_object_gemini:{object_name}", model).lower()
