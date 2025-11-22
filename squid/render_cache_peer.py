#!/usr/bin/env python3
"""Render Squid cache_peer configuration from UPSTREAM_PROXY_URLS."""

from __future__ import annotations

import os
import sys
from urllib.parse import urlparse


def _parse_urls(raw: str) -> list[str]:
    urls = []
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "://" not in chunk:
            chunk = f"http://{chunk}"
        urls.append(chunk)
    return urls


def _render(urls: list[str]) -> str:
    lines: list[str] = []
    multi_peer = len(urls) > 1

    for idx, url in enumerate(urls, start=1):
        parsed = urlparse(url)
        if not parsed.hostname or not parsed.port:
            raise ValueError(f"UPSTREAM proxy URL missing host/port: {url!r}")
        login_clause = ""
        if parsed.username:
            password = parsed.password or ""
            login_clause = f" login={parsed.username}:{password}"
        peer_name = f"upstream{idx}"
        extra = " round-robin" if multi_peer else ""
        line = (
            f"cache_peer {parsed.hostname} parent {parsed.port} 0"
            f" proxy-only no-query no-digest{extra} name={peer_name}{login_clause}"
        )
        lines.append(line)
        lines.append(f"cache_peer_access {peer_name} allow all")
    return "\n".join(lines)


def main() -> None:
    raw = os.environ.get("UPSTREAM_PROXY_URLS", "").strip()
    if not raw:
        raise SystemExit("UPSTREAM_PROXY_URLS must be set with at least one proxy URL")
    urls = _parse_urls(raw)
    if not urls:
        raise SystemExit("UPSTREAM_PROXY_URLS did not contain any usable entries")
    try:
        rendered = _render(urls)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    print(rendered)


if __name__ == "__main__":
    main()
