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
    """Thin HTTP client wrapper for SerpApi."""

    BASE_URL = "https://serpapi.com/search.json"
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
        self.api_key = api_key or os.getenv("SERPAPI_KEY")
        if not self.api_key:
            raise SerpApiConfigError("SERPAPI_KEY environment variable is not set.")

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
        params = {
            "engine": self.engine,
            "api_key": self.api_key,
            "q": query,
            "location": extra_params.pop("location", self.location),
            "gl": extra_params.pop("gl", self.gl),
            "hl": extra_params.pop("hl", self.hl),
            "num": extra_params.pop("num", 10),
        }
        params.update(extra_params)

        try:
            self.logger.info(
                "Issuing SerpApi request query=%s location=%s num=%s",
                query,
                params.get("location"),
                params.get("num"),
            )
            response = requests.get(self.BASE_URL, params=params, timeout=self.timeout)
        except requests.RequestException as exc:
            self.logger.warning("SerpApi network error for query=%s: %s", query, exc)
            raise SerpApiError(f"SerpApi request failed for '{query}': {exc}") from exc

        if response.status_code == 429:
            self.logger.error("SerpApi rate limit hit for query=%s", query)
            raise SerpApiQuotaError("SerpApi rate limit exceeded.")
        if response.status_code == 403:
            self.logger.error("SerpApi API key rejected or quota exhausted for query=%s", query)
            raise SerpApiQuotaError("SerpApi API key rejected or quota exhausted.")
        if response.status_code >= 500:
            self.logger.error(
                "SerpApi server error status=%s for query=%s", response.status_code, query
            )
            raise SerpApiError(f"SerpApi server error ({response.status_code}).")
        if response.status_code != 200:
            self.logger.error(
                "SerpApi unexpected status=%s for query=%s body=%s",
                response.status_code,
                query,
                response.text[:200],
            )
            raise SerpApiError(
                f"SerpApi returned HTTP {response.status_code}: {response.text[:200]}"
            )

        try:
            payload: Dict[str, Any] = response.json()
        except ValueError as exc:
            self.logger.error("SerpApi JSON decode failed for query=%s: %s", query, exc)
            raise SerpApiError("Failed to decode SerpApi response as JSON.") from exc

        error_message = payload.get("error")
        if error_message:
            lowered = error_message.lower()
            if "quota" in lowered or "payment" in lowered:
                self.logger.error(
                    "SerpApi reported quota issue for query=%s: %s", query, error_message
                )
                raise SerpApiQuotaError(error_message)
            if "api key" in lowered:
                self.logger.error(
                    "SerpApi reported configuration error for query=%s: %s",
                    query,
                    error_message,
                )
                raise SerpApiConfigError(error_message)
            self.logger.error(
                "SerpApi reported error for query=%s: %s", query, error_message
            )
            raise SerpApiError(error_message)

        self.logger.info(
            "SerpApi request succeeded query=%s search_id=%s organic_results=%s",
            query,
            payload.get("search_metadata", {}).get("id"),
            len(payload.get("organic_results") or []),
        )
        return payload
