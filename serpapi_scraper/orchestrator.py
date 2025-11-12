import logging
import os
import re
import sys
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import unquote, urlsplit

import requests
from pypdf import PdfReader

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
from app.config import DOWNLOAD_TIMEOUT, USER_AGENT

PdfResult = Dict[str, Any]

logger = logging.getLogger("serpapi.orchestrator")


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
}


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


def evaluate_pdf_candidate(
    local_path: str,
    model: str,
    candidate_doc_type: Optional[str],
) -> Dict[str, Any]:
    """
    Determine whether the downloaded PDF looks like an acceptable manual and resolve its doc_type.

    Returns analysis dict with accept flag, resolved doc_type, and supporting metadata.
    """
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
    language_hits = features.get("language_hits", {})
    english_hits = language_hits.get("english", 0)
    spanish_hits = language_hits.get("spanish", 0)
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
    elif english_hits == 0 and spanish_hits > 0:
        accept = False
        reason = "non_english_content"
    elif spanish_hits >= max(3, english_hits * 2):
        accept = False
        reason = "non_english_content"

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
        if not is_probable_pdf(url):
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
    headers = {"User-Agent": USER_AGENT, "Accept-Language": DEFAULT_ACCEPT_LANGUAGE}
    logger.info("Downloading candidate url=%s brand=%s model=%s", url, brand, model)
    try:
        response = requests.get(
            url,
            headers=headers,
            stream=True,
            timeout=DOWNLOAD_TIMEOUT,
            allow_redirects=True,
        )
    except requests.RequestException as exc:
        logger.warning("Download failed for url=%s: %s", url, exc)
        if should_use_headless(url):
            logger.info("Attempting headless fallback download for url=%s", url)
            referer = infer_headless_referer(url)
            return download_pdf_with_headless(url, temp_dir, referer=referer)
        return None

    if response.status_code != 200:
        logger.info(
            "Non-200 response while downloading url=%s status=%s",
            url,
            response.status_code,
        )
        redirected_url = response.url or url
        if response.status_code in {401, 403, 404, 407, 408, 429, 500} and should_use_headless(
            redirected_url
        ):
            logger.info(
                "Attempting headless fallback due to status=%s url=%s",
                response.status_code,
                redirected_url,
            )
            referer = infer_headless_referer(url) or infer_headless_referer(redirected_url)
            return download_pdf_with_headless(redirected_url, temp_dir, referer=referer)
        return None

    content_type = (response.headers.get("Content-Type") or "").lower()
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
        local_path = download_pdf(candidate["url"], temp_dir, brand=brand, model=model)
        if not local_path:
            cleanup_temp_dir(temp_dir)
            return None

        if not validate_pdf_file(local_path):
            logger.info("Validation failed for candidate url=%s", candidate.get("url"))
            cleanup_temp_dir(temp_dir)
            return None

        analysis = evaluate_pdf_candidate(
            local_path,
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
            "source_url": candidate.get("url"),
            "file_url": candidate.get("url"),
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
) -> Optional[PdfResult]:
    """
    Attempt to fetch a manual via SerpApi for the provided brand/model.

    Returns a result dict compatible with validate_and_ingest_manual or None if no
    suitable PDF was found.
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

    for index, query in enumerate(queries, start=1):
        logger.info("SerpApi query %d/%d: %s", index, len(queries), query)
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

        # Sort by descending score to try the most promising PDFs first.
        candidates.sort(key=lambda item: item.get("score", 0), reverse=True)
        for candidate in candidates[:5]:
            result = attempt_candidate(candidate, brand=brand_lower, model=model)
            if result:
                logger.info(
                    "Candidate accepted url=%s brand=%s model=%s",
                    candidate.get("url"),
                    brand,
                    model,
                )
                return result
            logger.info(
                "Candidate rejected after validation url=%s brand=%s model=%s",
                candidate.get("url"),
                brand,
                model,
            )

    logger.info("No valid SerpApi manual found for brand=%s model=%s", brand, model)
    return None


__all__ = [
    "fetch_manual_with_serpapi",
    "SerpApiClient",
    "SerpApiError",
    "SerpApiConfigError",
    "SerpApiQuotaError",
]
