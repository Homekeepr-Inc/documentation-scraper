#!/usr/bin/env python3
"""
Bootstrap script that assigns a deterministic proxy profile per container
before launching the main application process.
"""

from __future__ import annotations

import os
import re
import sys
from typing import List


def _default_cmd() -> List[str]:
    return [
        "uvicorn",
        "app.main:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
    ]
PROFILE_ENV = "PROXY_PROFILE_NAMES"


def _slug_to_env(name: str) -> str:
    return re.sub(r"[^A-Z0-9]", "_", name.upper())


def _parse_profiles() -> List[str]:
    raw = os.getenv(PROFILE_ENV, "")
    profiles = [chunk.strip() for chunk in raw.split(",") if chunk.strip()]
    return profiles


def _host_index(hostname: str) -> int:
    match = re.search(r"(\d+)$", hostname)
    if match:
        # Compose hostnames are 1-indexed (service_1, service_2, ...)
        return max(int(match.group(1)) - 1, 0)
    # Fallback to deterministic hash
    return sum(ord(ch) for ch in hostname) if hostname else 0


def _apply_profile(profile: str) -> None:
    safe = _slug_to_env(profile)
    squid_url = os.getenv(f"PROXY_{safe}_SQUID_URL")
    public_url = os.getenv(f"PROXY_{safe}_PUBLIC_URL")
    proxy_type = os.getenv(f"PROXY_{safe}_TYPE", "HTTP").upper()

    if squid_url:
        os.environ["PROXY_URL"] = squid_url
    if public_url:
        os.environ["TWO_CAPTCHA_PROXY"] = public_url
        os.environ["TWO_CAPTCHA_PROXY_TYPE"] = proxy_type
    os.environ["CURRENT_PROXY_PROFILE"] = profile


def _log_assignment(hostname: str, profile: str) -> None:
    msg = f"[proxy-bootstrap] hostname={hostname} profile={profile}"
    print(msg, flush=True)


def main() -> None:
    cmd = sys.argv[1:] or _default_cmd()
    hostname = os.getenv("HOSTNAME", "")
    profiles = _parse_profiles()

    if profiles:
        idx = _host_index(hostname)
        profile = profiles[idx % len(profiles)]
        _apply_profile(profile)
        _log_assignment(hostname, profile)

    os.execvp(cmd[0], cmd)


if __name__ == "__main__":
    main()
