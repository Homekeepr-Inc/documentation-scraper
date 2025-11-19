import base64
import contextlib
import logging
import os
import re
import sys
import tempfile
from functools import lru_cache
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple
from urllib.parse import unquote, urlsplit

import requests
from pypdf import PdfReader, PdfWriter

from .client import SerpApiClient, SerpApiConfigError, SerpApiError, SerpApiQuotaError
from .config import BrandConfig, build_queries, get_brand_config

# Reuse existing scraper utilities for temp dir management and PDF validation.
HEADLESS_UTILS_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "headless-browser-scraper")
)
if HEADLESS_UTILS_PATH not in sys.path:
    sys.path.append(HEADLESS_UTILS_PATH)

from utils import (  # type: ignore  # pylint: disable=import-error
    cleanup_temp_dir,
    create_temp_download_dir,
    validate_pdf_file,
)
from .headless_pdf_fetcher import download_pdf_with_headless, get_host
from .manualslib_scraper import (
    ManualslibDownload,
    download_manual_from_product_page,
    is_manualslib_product_url,
)
from .searspartsdirect_scraper import (
    SearsPartsDirectDownload,
    download_manual_from_product_page as download_searspartsdirect_from_page,
    is_searspartsdirect_manual_page,
)
from app.config import DOWNLOAD_TIMEOUT, USER_AGENT, PROXY_URL

PdfResult = Dict[str, Any]
FallbackQueryProvider = Callable[[BrandConfig, str], List[str]]

logger = logging.getLogger("serpapi.orchestrator")


def _env_flag(name: str, default: bool = False) -> bool:
    raw = (os.getenv(name) or "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


# Simple keyword mapping to infer document type heuristically.
DOC_TYPE_KEYWORDS: Dict[str, Iterable[str]] = {
    "owner": ("owner", "owners", "use and care", "use & care"),
    "installation": ("installation", "install", "mounting"),
    "tech": ("tech sheet", "technical", "service manual", "service data"),
    "spec": ("spec", "specification", "dimension", "datasheet"),
    "guide": ("quick start", "quick-start", "cycle guide", "guide"),
    "parts": (
        "parts manual",
        "parts list",
        "parts catalog",
        "parts catalogue",
        "parts diagram",
        "replacement parts",
        "service parts",
        "parts breakdown",
        "parts",
    ),
}

# Additional PDF content heuristics to validate we captured an actual manual.
PDF_KEYWORDS: Dict[str, Tuple[str, ...]] = {
    "owner": (
        "owner's manual",
        "owners manual",
        "owner manual",
        "use and care",
        "use & care",
        "user manual",
        "user guide",
        "instruction manual",
        "operating instructions",
        "operation manual",
        "instruction booklet",
        "installation and operation manual",
        "maintenance and care",
    ),
    "installation": (
        "installation instructions",
        "installation manual",
        "installation guide",
        "install this water heater",
        "install the appliance",
        "venting instructions",
        "setup instructions",
        "installation requirements",
    ),
    "tech": (
        "service manual",
        "service information",
        "technical service",
        "troubleshooting guide",
        "wiring diagram",
        "parts list",
        "diagnostic codes",
    ),
    "guide": (
        "quick start guide",
        "quick reference guide",
        "cycle guide",
        "use guide",
    ),
    "parts": (
        "parts manual",
        "parts list",
        "parts catalog",
        "parts catalogue",
        "parts diagram",
        "exploded view",
        "replacement parts",
        "service parts",
        "parts breakdown",
    ),
}

MARKETING_KEYWORDS: Tuple[str, ...] = (
    "brochure",
    "brochures",
    "product overview",
    "sell sheet",
    "sell-sheet",
    "sales sheet",
    "marketing",
    "catalog",
    "fact sheet",
    "spec sheet",
    "specification sheet",
    "datasheet",
    "feature highlights",
    "product highlights",
    "promo",
)

MANUAL_TOKENS: Tuple[str, ...] = (
    "manual",
    "instructions",
    "guide",
    "use and care",
    "use & care",
)

MAX_ANALYZED_PAGES = 6
MAX_ANALYZED_CHARACTERS = 20000
ACCEPTABLE_DOC_TYPES = {"owner"}
DISALLOWED_DOC_TYPES = {"parts"}
DISALLOWED_LOCALE_SUBSTRINGS = ("/es-mx/",)
LANGUAGE_KEYWORDS: Dict[str, Tuple[str, ...]] = {
    "english": (
        "warning",
        "caution",
        "read and save these instructions",
        "important safety instructions",
        "english",
        "customer care",
        "service and support",
    ),
    "spanish": (
        "manual de",
        "instrucciones de",
        "en español",
        "advertencia",
        "precaución",
        "peligro",
        "seguridad",
        "guarde estas instrucciones",
        "español",
    ),
}
DEFAULT_ACCEPT_LANGUAGE = "en-US,en;q=0.9"
HEADLESS_FALLBACK_HOSTS = {
    "whirlpool.com",
    "www.whirlpool.com",
    "lowes.com",
    "www.lowes.com",
    "pdf.lowes.com",
}

HOST_PREFLIGHT_URLS: Dict[str, str] = {
    "whirlpool.com": "https://www.whirlpool.com/",
    "www.whirlpool.com": "https://www.whirlpool.com/",
    "lowes.com": "https://www.lowes.com/",
    "www.lowes.com": "https://www.lowes.com/",
    "pdf.lowes.com": "https://www.lowes.com/",
}

BROWSER_SEC_CH_HEADERS = {
    "sec-ch-ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
}


def default_fallback_query_provider(config: BrandConfig, model: str) -> List[str]:
    """Default fallback queries (SearsPartsDirect) used when primary searches return nothing."""

    normalized_model = model.strip()
    manual_phrase = "owner's manual"
    subject_parts = []
    if config.display_name:
        subject_parts.append(config.display_name.strip())
    if normalized_model:
        subject_parts.append(normalized_model)
    subject = " ".join(part for part in subject_parts if part)
    if subject:
        query = f"{subject} {manual_phrase} site:searspartsdirect.com"
    else:
        query = f"{manual_phrase} site:searspartsdirect.com"
    return [query]

# Gate the Gemini flow behind env flags so production defaults stay unchanged.
USE_GEMINI_VALIDATION = _env_flag("SERPAPI_USE_GEMINI_VALIDATION", False)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL_NAME = os.getenv("SERPAPI_GEMINI_MODEL", "models/gemini-2.5-flash")
GEMINI_PAGE_LIMIT = int(os.getenv("SERPAPI_GEMINI_PAGE_LIMIT", "5") or "5")
if GEMINI_PAGE_LIMIT <= 0:
    GEMINI_PAGE_LIMIT = 5
GEMINI_PROMPT_TEMPLATE = (
    os.getenv("SERPAPI_GEMINI_PROMPT")
    or (
        "You are checking whether a PDF contains the owner's manual for a specific appliance. "
        "Respond with a single word: 'yes' if the document is the owner's manual for the given brand "
        "and model, otherwise respond 'no'. Do not add explanations."
    )
)
GEMINI_REQUEST_TIMEOUT = int(os.getenv("SERPAPI_GEMINI_TIMEOUT", "45") or "45")
GEMINI_LOGGER = logging.getLogger("serpapi.gemini")
GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta"


@lru_cache(maxsize=1)
def _gemini_enabled() -> bool:
    """Resolve whether Gemini can be used, logging once if misconfigured."""
    if not USE_GEMINI_VALIDATION:
        return False
    if not GEMINI_API_KEY:
        GEMINI_LOGGER.error(
            "SERPAPI_USE_GEMINI_VALIDATION enabled but GEMINI_API_KEY is not set; disabling Gemini validation."
        )
        return False
    return True


def _build_pdf_excerpt(local_path: str, page_limit: int) -> Tuple[str, bool]:
    """Trim large PDFs down to the first N pages since Gemini pricing scales with file size."""
    reader = PdfReader(local_path)
    total = len(reader.pages)
    if total <= page_limit:
        return local_path, False

    writer = PdfWriter()
    for page in reader.pages[:page_limit]:
        writer.add_page(page)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        writer.write(temp_file)  # type: ignore[arg-type]
        excerpt_path = temp_file.name
    return excerpt_path, True


def _run_gemini_validation(pdf_path: str, brand: str, model: str) -> Tuple[Optional[bool], str]:
    """Upload the excerpt and normalize Gemini's response to a boolean."""
    prompt = f"{GEMINI_PROMPT_TEMPLATE}\nBrand: {brand}\nModel: {model}"
    try:
        with open(pdf_path, "rb") as pdf_handle:
            encoded = base64.b64encode(pdf_handle.read()).decode("utf-8")
    except OSError as exc:
        GEMINI_LOGGER.warning(
            "Failed to read PDF for Gemini validation path=%s error=%s", pdf_path, exc
        )
        return None, ""

    request_body = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": prompt},
                    {
                        "inlineData": {
                            "mimeType": "application/pdf",
                            "data": encoded,
                        }
                    },
                ],
            }
        ]
    }

    url = f"{GEMINI_ENDPOINT}/{GEMINI_MODEL_NAME}:generateContent?key={GEMINI_API_KEY}"
    try:
        response = requests.post(
            url,
            json=request_body,
            timeout=GEMINI_REQUEST_TIMEOUT,
        )
        response.raise_for_status()
    except Exception as exc:  # pylint: disable=broad-except
        GEMINI_LOGGER.warning(
            "Gemini validation failed brand=%s model=%s error=%s", brand, model, exc
        )
        return None, ""

    payload = response.json()
    candidates = payload.get("candidates") or []
    if not candidates:
        GEMINI_LOGGER.warning(
            "Gemini response missing candidates brand=%s model=%s payload=%s",
            brand,
            model,
            payload,
        )
        return None, ""

    text_response = ""
    first_candidate = candidates[0]
    parts = (first_candidate.get("content") or {}).get("parts") if isinstance(first_candidate, dict) else None
    if parts:
        for part in parts:
            text = part.get("text")
            if text:
                text_response = text.strip()
                break

    normalized = text_response.lower()
    if "yes" in normalized.split():
        return True, text_response
    if "no" in normalized.split():
        return False, text_response
    if "yes" in normalized:
        return True, text_response
    if "no" in normalized:
        return False, text_response
    return None, text_response


def build_browser_headers(referer: Optional[str]) -> Dict[str, str]:
    headers: Dict[str, str] = {
        "User-Agent": USER_AGENT,
        "Accept": "application/pdf,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": DEFAULT_ACCEPT_LANGUAGE,
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-User": "?1",
    }
    headers.update(BROWSER_SEC_CH_HEADERS)
    if referer:
        headers["Referer"] = referer
        headers["Sec-Fetch-Site"] = "same-origin"
    else:
        headers["Sec-Fetch-Site"] = "none"
    return headers


def warm_up_session_for_host(
    session: requests.Session,
    url: str,
    *,
    timeout: Tuple[int, int] = (5, 15),
) -> Optional[str]:
    """Perform a light navigation to establish cookies before the PDF request."""

    host = get_host(url)
    warmup_url = HOST_PREFLIGHT_URLS.get(host)
    if not warmup_url:
        return None

    warmup_headers = build_browser_headers(None)
    warmup_headers.pop("Sec-Fetch-User", None)
    warmup_headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"

    try:
        response = session.get(
            warmup_url,
            headers=warmup_headers,
            allow_redirects=True,
            timeout=timeout,
        )
        logger.debug(
            "Warm-up request completed host=%s status=%s final_url=%s",
            host,
            response.status_code,
            response.url,
        )
        if response.status_code < 400:
            return response.url or warmup_url
    except requests.RequestException as exc:  # pylint: disable=broad-except
        logger.debug(
            "Warm-up request failed host=%s url=%s error=%s",
            host,
            warmup_url,
            exc,
        )
    return None


def detect_doc_type(title: str, url: str) -> str:
    combined = f"{title} {url}".lower()
    # Treat parts signals as a hard override so they are never mistaken for owner manuals.
    parts_keywords = DOC_TYPE_KEYWORDS.get("parts", ())
    if any(keyword in combined for keyword in parts_keywords):
        return "parts"

    doc_type_scores: Dict[str, int] = {}
    for doc_type, keywords in DOC_TYPE_KEYWORDS.items():
        if doc_type == "parts":
            continue
        hits = sum(1 for keyword in keywords if keyword in combined)
        if hits:
            doc_type_scores[doc_type] = hits

    if not doc_type_scores:
        return "owner"

    # Prefer acceptable doc types when there is a tie; otherwise choose the highest score.
    best_doc_type, _ = max(
        doc_type_scores.items(),
        key=lambda item: (item[0] in ACCEPTABLE_DOC_TYPES, item[1]),
    )
    return best_doc_type


def is_probable_pdf(url: str) -> bool:
    sanitized = url.lower().split("?", 1)[0]
    return sanitized.endswith(".pdf")


def is_allowed_html_candidate(url: str) -> bool:
    return is_manualslib_product_url(url) or is_searspartsdirect_manual_page(url)


def derive_filename(url: str, brand: str, model: str) -> str:
    path = urlsplit(url).path
    filename = os.path.basename(path)
    if not filename or "." not in filename:
        slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", f"{brand}-{model}") or "manual"
        filename = f"{slug}.pdf"
    if not filename.lower().endswith(".pdf"):
        filename += ".pdf"
    return unquote(filename)


def should_use_headless(url: str) -> bool:
    host = get_host(url)
    return host in HEADLESS_FALLBACK_HOSTS


def _is_forbidden_status(status: Optional[int]) -> bool:
    return status == 403


def _exception_suggests_forbidden(exc: Exception) -> bool:
    response = getattr(exc, "response", None)
    if response is not None and getattr(response, "status_code", None) == 403:
        return True
    # Proxy errors frequently embed the HTTP status in the message text.
    return "403" in str(exc)


def is_disallowed_locale_url(url: str) -> bool:
    lowered = url.lower()
    return any(segment in lowered for segment in DISALLOWED_LOCALE_SUBSTRINGS)


def infer_headless_referer(url: str) -> Optional[str]:
    try:
        parsed = urlsplit(url)
    except Exception:  # pylint: disable=broad-except
        return None
    scheme = parsed.scheme or "https"
    host = parsed.netloc
    if not host:
        host = get_host(url)
    if not host:
        return None
    return f"{scheme}://{host}/"


def score_candidate(url: str, title: str, snippet: str, config: BrandConfig, model: str, position: Optional[int]) -> int:
    score = 0
    lowered_url = url.lower()
    lowered_title = title.lower()
    lowered_snippet = snippet.lower()
    model_lower = model.lower()

    if model_lower and model_lower in lowered_url:
        score += 40
    if model_lower and model_lower in lowered_title:
        score += 30
    if model_lower and model_lower in lowered_snippet:
        score += 20

    for domain in config.domains:
        if domain.lower() in lowered_url:
            score += 20

    doc_type = detect_doc_type(title, url)
    if doc_type == "owner":
        score += 30
    elif doc_type in DISALLOWED_DOC_TYPES:
        score -= 40
    else:
        score -= 10

    parts_hits = (
        lowered_url.count("parts")
        + lowered_title.count("parts")
        + lowered_snippet.count("parts")
    )
    if parts_hits:
        score -= min(60, parts_hits * 10)

    if is_disallowed_locale_url(url):
        score -= 80

    if position is not None:
        score += max(0, 12 - position)

    return score


def extract_pdf_features(local_path: str, model: str) -> Optional[Dict[str, Any]]:
    """Extract keyword signals from the early pages of the PDF to validate its type."""
    try:
        reader = PdfReader(local_path)
    except Exception as exc:  # pylint: disable=broad-except
        logger.warning("Failed to open PDF for analysis path=%s: %s", local_path, exc)
        return None

    page_count = len(reader.pages)
    collected_text: List[str] = []
    char_budget = 0
    for page_index, page in enumerate(reader.pages[:MAX_ANALYZED_PAGES]):
        try:
            extracted = page.extract_text() or ""
        except Exception as exc:  # pylint: disable=broad-except
            logger.debug(
                "Error extracting text from page %s path=%s: %s", page_index, local_path, exc
            )
            continue

        collected_text.append(extracted)
        char_budget += len(extracted)
        if char_budget >= MAX_ANALYZED_CHARACTERS:
            break

    combined_text = " ".join(collected_text).lower()
    keyword_hits: Dict[str, int] = {}
    for doc_type, keywords in PDF_KEYWORDS.items():
        keyword_hits[doc_type] = sum(1 for keyword in keywords if keyword in combined_text)

    marketing_hits = sum(1 for keyword in MARKETING_KEYWORDS if keyword in combined_text)
    manual_tokens = sum(1 for token in MANUAL_TOKENS if token in combined_text)
    contains_model = bool(model) and model.lower() in combined_text
    language_hits: Dict[str, int] = {}
    for language, keywords in LANGUAGE_KEYWORDS.items():
        language_hits[language] = sum(1 for keyword in keywords if keyword in combined_text)

    return {
        "page_count": page_count,
        "keyword_hits": keyword_hits,
        "marketing_hits": marketing_hits,
        "manual_tokens": manual_tokens,
        "contains_model": contains_model,
        "text_sample_present": bool(collected_text),
        "language_hits": language_hits,
        "fallback_image_manual": False,
    }


def evaluate_pdf_candidate_with_gemini(
    local_path: str,
    brand: str,
    model: str,
    candidate_doc_type: Optional[str],
) -> Dict[str, Any]:
    """Use Gemini yes/no classification while still recording the usual PDF metadata."""
    extracted_features = extract_pdf_features(local_path, model)
    if extracted_features is None:
        return {
            "accept": False,
            "reason": "analysis_failed",
            "resolved_doc_type": None,
            "features": None,
        }

    features = dict(extracted_features)
    features.setdefault("keyword_hits", {})
    features.setdefault("marketing_hits", 0)
    features.setdefault("manual_tokens", 0)
    features.setdefault("contains_model", False)
    features.setdefault("text_sample_present", False)
    features.setdefault("language_hits", {})
    features.setdefault("fallback_image_manual", False)

    page_count = int(features.get("page_count") or 0)
    features["too_short_for_owner"] = page_count < 4

    if page_count < 4:
        return {
            "accept": False,
            "reason": "owner_manual_too_short",
            "resolved_doc_type": None,
            "features": features,
        }

    excerpt_path, created_excerpt = _build_pdf_excerpt(local_path, GEMINI_PAGE_LIMIT)
    try:
        result, response_text = _run_gemini_validation(excerpt_path, brand, model)
    finally:
        if created_excerpt:
            with contextlib.suppress(OSError):
                os.unlink(excerpt_path)

    features["gemini_model"] = GEMINI_MODEL_NAME
    features["gemini_page_limit"] = min(GEMINI_PAGE_LIMIT, page_count)
    features["gemini_response"] = response_text

    if result is None:
        return {
            "accept": False,
            "reason": "gemini_inconclusive",
            "resolved_doc_type": None,
            "features": features,
        }

    features["gemini_answer"] = "yes" if result else "no"

    if not result:
        return {
            "accept": False,
            "reason": "gemini_rejected",
            "resolved_doc_type": None,
            "features": features,
        }

    resolved_doc_type = (candidate_doc_type or "").lower() or "owner"
    if resolved_doc_type not in ACCEPTABLE_DOC_TYPES:
        resolved_doc_type = "owner"

    return {
        "accept": True,
        "reason": None,
        "resolved_doc_type": resolved_doc_type,
        "features": features,
    }


def evaluate_pdf_candidate(
    local_path: str,
    brand: str,
    model: str,
    candidate_doc_type: Optional[str],
) -> Dict[str, Any]:
    """
    Determine whether the downloaded PDF looks like an acceptable manual and resolve its doc_type.

    Returns analysis dict with accept flag, resolved doc_type, and supporting metadata.
    """
    if _gemini_enabled():
        return evaluate_pdf_candidate_with_gemini(
            local_path,
            brand,
            model,
            candidate_doc_type,
        )

    features = extract_pdf_features(local_path, model)
    if not features:
        return {
            "accept": False,
            "reason": "analysis_failed",
            "resolved_doc_type": None,
            "features": None,
        }

    keyword_hits = features["keyword_hits"]
    manual_signal = sum(keyword_hits.get(doc_type, 0) for doc_type in ACCEPTABLE_DOC_TYPES)
    manual_tokens = features["manual_tokens"]
    marketing_hits = features["marketing_hits"]
    page_count = features["page_count"]
    # language_hits = features.get("language_hits", {})
    # english_hits = language_hits.get("english", 0)
    # spanish_hits = language_hits.get("spanish", 0)
    # total_language_hits = english_hits + spanish_hits
    # english_ratio = (
    #     english_hits / total_language_hits if total_language_hits else 0.0
    # )
    # Only reject for Spanish dominance when English is truly scarce (<20%) so mixed manuals remain eligible.
    # Heuristic to avoid counting promo / non owners-manual PDFs incorrectly.
    features["too_short_for_owner"] = page_count < 4

    candidate_doc_type_normalized = (candidate_doc_type or "").lower() or None
    resolved_doc_type = candidate_doc_type_normalized or "owner"
    top_doc_type, top_hits = max(
        keyword_hits.items(), key=lambda item: item[1], default=(resolved_doc_type, 0)
    )
    disallowed_hit_total = sum(
        keyword_hits.get(doc_type, 0) for doc_type in DISALLOWED_DOC_TYPES
    )

    if top_hits > 0:
        if top_doc_type in DISALLOWED_DOC_TYPES:
            resolved_doc_type = top_doc_type
        elif top_doc_type in ACCEPTABLE_DOC_TYPES:
            resolved_doc_type = top_doc_type

    if (
        resolved_doc_type not in ACCEPTABLE_DOC_TYPES
        and resolved_doc_type not in DISALLOWED_DOC_TYPES
        and keyword_hits.get("owner")
        and disallowed_hit_total == 0
    ):
        resolved_doc_type = "owner"

    has_manual_tokens = manual_tokens > 0
    accept = resolved_doc_type in ACCEPTABLE_DOC_TYPES and (
        manual_signal > 0
        or (resolved_doc_type == "owner" and has_manual_tokens)
    )
    reason = None

    if resolved_doc_type not in ACCEPTABLE_DOC_TYPES:
        accept = False
        reason = f"disallowed_doc_type:{resolved_doc_type}"
    elif resolved_doc_type == "owner" and page_count < 4:
        accept = False
        reason = "owner_manual_too_short"
    elif manual_signal == 0 and not (resolved_doc_type == "owner" and has_manual_tokens):
        accept = False
        reason = "no_manual_keywords"
    elif marketing_hits and keyword_hits.get("owner", 0) == 0:
        accept = False
        reason = "marketing_signals"
    elif page_count <= 2 and keyword_hits.get("owner", 0) == 0:
        accept = False
        reason = "insufficient_pages"
    # removed because it has a bad hit rate
    # elif english_hits == 0 and spanish_hits > 0:
    #     accept = False
    #     reason = "non_english_content"
    # elif english_ratio < 0.2 and spanish_hits >= max(3, english_hits * 2):
    #     accept = False
    #     reason = "non_english_content"

    if (
        not accept
        and reason == "no_manual_keywords"
        and not features["text_sample_present"]
        and page_count >= 5
    ):
        # Fallback for image-only manuals lacking extractable text but long enough to be plausible.
        resolved_doc_type = (
            resolved_doc_type if resolved_doc_type in ACCEPTABLE_DOC_TYPES else "owner"
        )
        accept = True
        reason = None
        features["fallback_image_manual"] = True

    analysis = {
        "accept": accept,
        "reason": reason,
        "resolved_doc_type": resolved_doc_type if accept else None,
        "features": features,
    }

    logger.info(
        "PDF analysis path=%s doc_type=%s accept=%s manual_signal=%s manual_tokens=%s marketing_hits=%s page_count=%s contains_model=%s",
        local_path,
        analysis["resolved_doc_type"] or resolved_doc_type,
        analysis["accept"],
        manual_signal,
        manual_tokens,
        marketing_hits,
        page_count,
        features["contains_model"],
    )
    if not accept and reason:
        logger.info("Rejecting PDF path=%s reason=%s", local_path, reason)
    return analysis


def build_candidate_dict(
    url: str,
    *,
    title: str,
    snippet: str,
    position: Optional[int],
    config: BrandConfig,
    model: str,
    query: str,
    search_id: Optional[str],
    source: str,
) -> Dict[str, Any]:
    candidate: Dict[str, Any] = {
        "url": url,
        "title": title,
        "snippet": snippet,
        "position": position,
        "doc_type": detect_doc_type(title, url),
        "score": score_candidate(url, title, snippet, config, model, position),
        "query": query,
        "search_id": search_id,
        "source": source,
    }
    return candidate


def collect_candidates(
    payload: Dict[str, Any],
    config: BrandConfig,
    model: str,
    query: str,
    seen_urls: set,
) -> List[Dict[str, Any]]:
    candidates: List[Dict[str, Any]] = []
    search_id = payload.get("search_metadata", {}).get("id")
    logger.info(
        "Collecting candidates for query=%s (search_id=%s)",
        query,
        search_id or "unknown",
    )

    for result in payload.get("organic_results", []) or []:
        url = result.get("link") or result.get("redirect_link")
        if not url or url in seen_urls:
            continue
        if not is_probable_pdf(url) and not is_allowed_html_candidate(url):
            logger.debug("Skipping candidate due to non-supported HTML url=%s", url)
            continue
        if is_disallowed_locale_url(url):
            logger.debug("Skipping candidate due to disallowed locale url=%s", url)
            continue
        seen_urls.add(url)
        title = result.get("title") or ""
        snippet = result.get("snippet") or ""
        position = result.get("position")
        candidates.append(
            build_candidate_dict(
                url=url,
                title=title,
                snippet=snippet,
                position=position,
                config=config,
                model=model,
                query=query,
                search_id=search_id,
                source="organic_results",
            )
        )
        logger.debug(
            "Queued organic candidate url=%s title=%s position=%s score=%s",
            url,
            title,
            position,
            candidates[-1]["score"],
        )

    for item in payload.get("inline_images", []) or []:
        url = item.get("source")
        if not url or url in seen_urls:
            continue
        if not is_probable_pdf(url):
            continue
        if is_disallowed_locale_url(url):
            logger.debug("Skipping inline candidate due to disallowed locale url=%s", url)
            continue
        seen_urls.add(url)
        title = item.get("title") or ""
        candidates.append(
            build_candidate_dict(
                url=url,
                title=title,
                snippet="",
                position=None,
                config=config,
                model=model,
                query=query,
                search_id=search_id,
                source="inline_images",
            )
        )
        logger.debug(
            "Queued inline candidate url=%s title=%s score=%s",
            url,
            title,
            candidates[-1]["score"],
        )

    logger.info(
        "Collected %d candidate(s) for query=%s (search_id=%s)",
        len(candidates),
        query,
        search_id or "unknown",
    )
    return candidates


def download_pdf(url: str, temp_dir: str, *, brand: str, model: str) -> Optional[str]:
    proxies = None
    if PROXY_URL:
        proxies = {"http": PROXY_URL, "https": PROXY_URL}
        logger.debug("Using configured proxy for direct PDF download proxy=%s", PROXY_URL)

    session = requests.Session()
    try:
        if proxies:
            session.proxies.update(proxies)

        referer = infer_headless_referer(url)
        warmed_referer = warm_up_session_for_host(session, url)
        if warmed_referer:
            if warmed_referer != referer:
                logger.debug(
                    "Using warmed referer for host url=%s referer=%s",
                    url,
                    warmed_referer,
                )
            referer = warmed_referer

        request_headers = build_browser_headers(referer)
        host = get_host(url)
        read_timeout = DOWNLOAD_TIMEOUT
        connect_timeout = min(10, DOWNLOAD_TIMEOUT)

        logger.info(
            "Downloading candidate url=%s brand=%s model=%s referer=%s read_timeout=%s",
            url,
            brand,
            model,
            referer or "none",
            read_timeout,
        )

        try:
            response = session.get(
                url,
                headers=request_headers,
                stream=True,
                timeout=(connect_timeout, read_timeout),
                allow_redirects=True,
            )
        except requests.ReadTimeout as exc:
            logger.warning(
                "Download timed out while reading url=%s host=%s read_timeout=%s error=%s",
                url,
                host,
                read_timeout,
                exc,
            )
            if should_use_headless(url):
                logger.info("Attempting headless fallback download for url=%s", url)
                return download_pdf_with_headless(url, temp_dir, referer=referer)
            return None
        except requests.RequestException as exc:
            logger.warning("Download failed for url=%s: %s", url, exc)
            force_headless = _exception_suggests_forbidden(exc)
            if should_use_headless(url) or force_headless:
                logger.info(
                    "Attempting headless fallback download for url=%s reason=%s",
                    url,
                    "forbidden" if force_headless else "allowlisted_host",
                )
                headless_referer = referer or infer_headless_referer(url)
                return download_pdf_with_headless(url, temp_dir, referer=headless_referer)
            return None

        if response.status_code != 200:
            logger.info(
                "Non-200 response while downloading url=%s status=%s",
                url,
                response.status_code,
            )
            redirected_url = response.url or url
            status_code = response.status_code
            force_headless = _is_forbidden_status(status_code)
            if status_code in {401, 403, 404, 407, 408, 429, 500} and (
                force_headless or should_use_headless(redirected_url)
            ):
                logger.info(
                    "Attempting headless fallback due to status=%s url=%s forced=%s",
                    status_code,
                    redirected_url,
                    force_headless,
                )
                referer = infer_headless_referer(url) or infer_headless_referer(redirected_url)
                return download_pdf_with_headless(redirected_url, temp_dir, referer=referer)
            return None

        content_type = (response.headers.get("Content-Type") or "").lower()
        logger.debug(
            "PDF response headers url=%s content_type=%s content_length=%s",
            url,
            content_type or "unknown",
            response.headers.get("Content-Length"),
        )
        if "pdf" not in content_type and not is_probable_pdf(response.url):
            logger.info(
                "Skipping candidate url=%s due to content-type=%s",
                url,
                content_type or "unknown",
            )
            redirected_url = response.url or url
            if should_use_headless(redirected_url):
                logger.info(
                    "Attempting headless fallback due to content-type=%s url=%s",
                    content_type or "unknown",
                    redirected_url,
                )
                referer = infer_headless_referer(url) or infer_headless_referer(redirected_url)
                return download_pdf_with_headless(redirected_url, temp_dir, referer=referer)
            return None

        filename = derive_filename(response.url or url, brand, model)
        destination = os.path.join(temp_dir, filename)

        try:
            with open(destination, "wb") as file_handle:
                for chunk in response.iter_content(chunk_size=8192):
                    if not chunk:
                        continue
                    file_handle.write(chunk)
        except OSError as exc:
            logger.error("Failed to persist PDF for url=%s: %s", url, exc)
            return None

        logger.info("Successfully downloaded url=%s to %s", url, destination)
        return destination
    finally:
        session.close()


def download_manualslib_candidate(
    product_url: str,
    download_dir: str,
) -> Optional[ManualslibDownload]:
    """
    Wrapper around download_manual_from_product_page with logging/guards so the orchestrator
    can treat ManualsLib URLs as first-class candidates.
    """

    if not product_url or not is_manualslib_product_url(product_url):
        return None

    logger.info("Detected ManualsLib candidate url=%s", product_url)
    try:
        return download_manual_from_product_page(
            product_url,
            download_dir=download_dir,
        )
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("ManualsLib download failed for url=%s: %s", product_url, exc)
        return None


# Go through the scrapers, falling back to the next one if we fail to fetch the right manual.
def attempt_candidate(candidate: Dict[str, Any], *, brand: str, model: str) -> Optional[PdfResult]:
    logger.info(
        "Attempting candidate url=%s score=%s source=%s",
        candidate.get("url"),
        candidate.get("score"),
        candidate.get("source"),
    )
    candidate_url = candidate.get("url") or ""
    if candidate_url and is_disallowed_locale_url(candidate_url):
        logger.info("Skipping candidate due to disallowed locale url=%s", candidate_url)
        return None
    temp_dir = create_temp_download_dir()
    try:
        manualslib_download: Optional[ManualslibDownload] = None
        searspartsdirect_download: Optional[SearsPartsDirectDownload] = None
        candidate_url = candidate.get("url") or ""

        # Start scraping. Add new fallback scrapers here. 
        if candidate_url:
            manualslib_download = download_manualslib_candidate(candidate_url, temp_dir)
            if not manualslib_download and is_manualslib_product_url(candidate_url):
                cleanup_temp_dir(temp_dir)
                return None
            if is_searspartsdirect_manual_page(candidate_url):
                searspartsdirect_download = download_searspartsdirect_from_page(
                    candidate_url,
                    download_dir=temp_dir,
                )
                if not searspartsdirect_download:
                    cleanup_temp_dir(temp_dir)
                    return None

        if manualslib_download:
            local_path = manualslib_download.pdf_path
            file_url = manualslib_download.download_url
            source_url = manualslib_download.manual_page_url
        elif searspartsdirect_download:
            local_path = searspartsdirect_download.pdf_path
            file_url = searspartsdirect_download.download_url
            source_url = searspartsdirect_download.product_url
        else:
            local_path = download_pdf(candidate["url"], temp_dir, brand=brand, model=model)
            if not local_path:
                cleanup_temp_dir(temp_dir)
                return None
            file_url = candidate.get("url")
            source_url = candidate.get("url")

        if not validate_pdf_file(local_path):
            logger.info("Validation failed for candidate url=%s", candidate.get("url"))
            cleanup_temp_dir(temp_dir)
            return None

        analysis = evaluate_pdf_candidate(
            local_path,
            brand,
            model,
            candidate.get("doc_type"),
        )
        if not analysis["accept"]:
            cleanup_temp_dir(temp_dir)
            return None

        resolved_doc_type = analysis["resolved_doc_type"] or candidate.get("doc_type") or "owner"

        result: PdfResult = {
            "brand": brand,
            "model_number": model,
            "doc_type": resolved_doc_type,
            "title": candidate.get("title") or f"{brand} {model} manual",
            "source_url": source_url,
            "file_url": file_url,
            "local_path": local_path,
            "serpapi_metadata": {
                "score": candidate.get("score"),
                "query": candidate.get("query"),
                "search_id": candidate.get("search_id"),
                "source": candidate.get("source"),
                "position": candidate.get("position"),
                "pdf_features": analysis["features"],
                "pdf_analysis_reason": analysis.get("reason"),
            },
        }
        if manualslib_download:
            result["serpapi_metadata"].update(
                {
                    "manualslib_product_url": manualslib_download.product_url,
                    "manualslib_manual_url": manualslib_download.manual_page_url,
                    "manualslib_download_url": manualslib_download.download_url,
                }
            )
        if searspartsdirect_download:
            result["serpapi_metadata"].update(
                {
                    "searspartsdirect_product_url": searspartsdirect_download.product_url,
                    "searspartsdirect_download_url": searspartsdirect_download.download_url,
                }
            )
        logger.info(
            "Validation passed for candidate url=%s doc_type=%s score=%s",
            candidate.get("url"),
            resolved_doc_type,
            candidate.get("score"),
        )
        return result
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception(
            "Unhandled error while processing candidate url=%s: %s",
            candidate.get("url"),
            exc,
        )
        cleanup_temp_dir(temp_dir)
        return None


def fetch_manual_with_serpapi(
    brand: str,
    model: str,
    *,
    client: Optional[SerpApiClient] = None,
    fallback_query_provider: Optional[FallbackQueryProvider] = None,
) -> Optional[PdfResult]:
    """
    Attempt to fetch a manual via SerpApi for the provided brand/model.

    Returns a result dict compatible with validate_and_ingest_manual or None if no
    suitable PDF was found. Provide fallback_query_provider to inject additional
    progressive search strings when the primary set yields no candidates.
    """
    logger.info("Starting SerpApi fetch brand=%s model=%s", brand, model)
    try:
        serpapi_client = client or SerpApiClient()
    except SerpApiConfigError as exc:
        logger.error("SerpApi disabled due to configuration error: %s", exc)
        return None

    brand_lower = (brand or "").lower()
    config = get_brand_config(brand_lower)
    queries = build_queries(config, model)
    if not queries:
        logger.warning(
            "No SerpApi queries constructed for brand=%s model=%s", brand, model
        )
        return None

    seen_urls: set = set()
    fallback_provider = fallback_query_provider or default_fallback_query_provider

    def run_query_batch(
        queries_to_try: List[str],
        *,
        batch_label: str,
    ) -> Tuple[Optional[PdfResult], bool]:
        had_candidates = False
        if not queries_to_try:
            return None, False

        for index, query in enumerate(queries_to_try, start=1):
            logger.info("%s query %d/%d: %s", batch_label, index, len(queries_to_try), query)
            try:
                payload = serpapi_client.search(query)
            except SerpApiQuotaError:
                logger.error("SerpApi quota exceeded during query=%s", query)
                raise
            except SerpApiError as exc:
                logger.warning("SerpApi search error for query=%s: %s", query, exc)
                continue

            candidates = collect_candidates(payload, config, model, query, seen_urls)
            if not candidates:
                logger.info("No PDF candidates returned for query=%s", query)
                continue

            had_candidates = True
            candidates.sort(key=lambda item: item.get("score", 0), reverse=True)
            for candidate in candidates[:5]:
                result = attempt_candidate(candidate, brand=brand_lower, model=model)
                if result:
                    logger.info(
                        "Candidate accepted url=%s brand=%s model=%s (batch=%s)",
                        candidate.get("url"),
                        brand,
                        model,
                        batch_label,
                    )
                    return result, True
                logger.info(
                    "Candidate rejected after validation url=%s brand=%s model=%s (batch=%s)",
                    candidate.get("url"),
                    brand,
                    model,
                    batch_label,
                )

        return None, had_candidates

    logger.debug(
        "Constructed SerpApi queries for brand=%s model=%s: %s",
        brand,
        model,
        queries,
    )
    logger.info(
        "Executing %d SerpApi querie(s) for brand=%s model=%s",
        len(queries),
        brand,
        model,
    )

    primary_result, primary_candidates_found = run_query_batch(queries, batch_label="SerpApi")
    if primary_result:
        return primary_result

    fallback_reason = (
        "returned candidates but none were valid"
        if primary_candidates_found
        else "returned no candidates"
    )
    fallback_queries = fallback_provider(config, model) if fallback_provider else []
    if not fallback_queries:
        logger.info(
            "Primary SerpApi search %s and no fallback queries were provided for brand=%s model=%s",
            fallback_reason,
            brand,
            model,
        )
        return None

    logger.info(
        "Primary SerpApi search %s; executing %d fallback querie(s)",
        fallback_reason,
        len(fallback_queries),
    )
    fallback_result, fallback_candidates_found = run_query_batch(
        fallback_queries,
        batch_label="Fallback",
    )
    if fallback_result:
        return fallback_result

    if fallback_candidates_found:
        logger.info(
            "Fallback SerpApi queries found candidates but none were valid for brand=%s model=%s",
            brand,
            model,
        )
    else:
        logger.info(
            "Fallback SerpApi queries returned no candidates for brand=%s model=%s",
            brand,
            model,
        )
    return None


__all__ = [
    "fetch_manual_with_serpapi",
    "SerpApiClient",
    "SerpApiError",
    "SerpApiConfigError",
    "SerpApiQuotaError",
]
