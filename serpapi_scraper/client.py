import logging
import os
from typing import Any, Dict, Optional

import requests


class SerpApiError(Exception):
    """Base SerpApi exception."""


class SerpApiConfigError(SerpApiError):
    """Raised when SerpApi is misconfigured (e.g., missing API key)."""


class SerpApiQuotaError(SerpApiError):
    """Raised when SerpApi quota or rate limits are exceeded."""


class SerpApiClient:
    """Thin HTTP client wrapper for Serper.dev (compatible with historic SerpApi interface)."""

    BASE_URL = "https://google.serper.dev/search"
    logger = logging.getLogger("serpapi.client")

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        engine: str = "google",
        location: str = "Austin, Texas, United States",
        gl: str = "us",
        hl: str = "en",
        timeout: int = 15,
    ) -> None:
        self.api_key = api_key or os.getenv("SERPER_API_KEY") or os.getenv("SERPAPI_KEY")
        if not self.api_key:
            raise SerpApiConfigError(
                "SERPER_API_KEY environment variable is not set (SERPAPI_KEY is also checked)."
            )

        self.engine = engine
        self.location = location
        self.gl = gl
        self.hl = hl
        self.timeout = timeout
        self.logger.debug(
            "SerpApiClient initialized engine=%s location=%s gl=%s hl=%s timeout=%s",
            self.engine,
            self.location,
            self.gl,
            self.hl,
            self.timeout,
        )

    def search(self, query: str, **extra_params: Any) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "q": query,
            "location": extra_params.pop("location", self.location),
            "gl": extra_params.pop("gl", self.gl),
            "hl": extra_params.pop("hl", self.hl),
            "num": extra_params.pop("num", 10),
        }
        payload.update(extra_params)
        # Remove falsy values because Serper rejects blank fields.
        payload = {key: value for key, value in payload.items() if value}

        try:
            self.logger.info(
                "Issuing Serper request query=%s location=%s num=%s",
                query,
                payload.get("location"),
                payload.get("num"),
            )
            response = requests.post(
                self.BASE_URL,
                headers={
                    "X-API-KEY": self.api_key,
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            self.logger.warning("Serper network error for query=%s: %s", query, exc)
            raise SerpApiError(f"Serper request failed for '{query}': {exc}") from exc

        if response.status_code == 429:
            self.logger.error("Serper rate limit hit for query=%s", query)
            raise SerpApiQuotaError("Serper rate limit exceeded.")
        if response.status_code in {401, 403}:
            self.logger.error("Serper API key rejected or quota exhausted for query=%s", query)
            raise SerpApiQuotaError("Serper API key rejected or quota exhausted.")
        if response.status_code >= 500:
            self.logger.error(
                "Serper server error status=%s for query=%s", response.status_code, query
            )
            raise SerpApiError(f"Serper server error ({response.status_code}).")
        if response.status_code != 200:
            self.logger.error(
                "Serper unexpected status=%s for query=%s body=%s",
                response.status_code,
                query,
                response.text[:200],
            )
            raise SerpApiError(
                f"Serper returned HTTP {response.status_code}: {response.text[:200]}"
            )

        try:
            payload: Dict[str, Any] = response.json()
        except ValueError as exc:
            self.logger.error("Serper JSON decode failed for query=%s: %s", query, exc)
            raise SerpApiError("Failed to decode Serper response as JSON.") from exc

        error_message = payload.get("error") or payload.get("message")
        if error_message:
            lowered = error_message.lower()
            if "quota" in lowered or "payment" in lowered:
                self.logger.error(
                    "Serper reported quota issue for query=%s: %s", query, error_message
                )
                raise SerpApiQuotaError(error_message)
            if "api key" in lowered:
                self.logger.error(
                    "Serper reported configuration error for query=%s: %s",
                    query,
                    error_message,
                )
                raise SerpApiConfigError(error_message)
            self.logger.error(
                "Serper reported error for query=%s: %s", query, error_message
            )
            raise SerpApiError(error_message)

        normalized_payload = self._normalize_serper_payload(payload)

        self.logger.info(
            "Serper request succeeded query=%s search_id=%s organic_results=%s credits=%s",
            query,
            normalized_payload.get("search_metadata", {}).get("id"),
            len(normalized_payload.get("organic_results") or []),
            payload.get("credits"),
        )
        return normalized_payload

    @staticmethod
    def _normalize_serper_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Map Serper response fields onto the previous SerpApi-compatible shape."""

        normalized = dict(payload)

        if "organic_results" not in normalized and payload.get("organic") is not None:
            normalized["organic_results"] = payload.get("organic") or []
        if "inline_images" not in normalized and payload.get("inlineImages") is not None:
            normalized["inline_images"] = payload.get("inlineImages") or []

        metadata = normalized.get("search_metadata")
        if metadata is None or not isinstance(metadata, dict):
            metadata = {}
            normalized["search_metadata"] = metadata

        metadata.setdefault(
            "id",
            payload.get("searchId")
            or payload.get("id")
            or (
                payload.get("searchParameters", {}).get("q")
                if isinstance(payload.get("searchParameters"), dict)
                else None
            ),
        )
        metadata.setdefault(
            "query",
            payload.get("searchParameters", {}).get("q")
            if isinstance(payload.get("searchParameters"), dict)
            else None,
        )
        metadata.setdefault("engine", "google")

        return normalized
