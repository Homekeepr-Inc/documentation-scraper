# ManualsLib Proxy & 2Captcha Strategy

This document explains how we keep Google reCAPTCHA happy while still rotating outbound proxies for ManualsLib scraping. The high‑level goal: every Selenium session and every 2Captcha worker must appear to come from the **same public proxy IP**, even though we run multiple app containers in parallel.

## Overview

1. **Multiple Squid instances.** Each Squid container (`squid-proxy-a`, `squid-proxy-b`, …) forwards traffic to a single upstream proxy defined via `UPSTREAM_PROXY_URLS`. This keeps the egress IP stable per Squid instance.
2. **Per-container assignment.** `bin/start_with_proxy.py` runs before the app starts. It reads `HOSTNAME` (`app-1`, `app-2`, …), selects a proxy profile from `PROXY_PROFILE_NAMES`, and exports:
   - `PROXY_URL` → internal Squid endpoint (e.g., `http://squid-proxy-a:8888`)
   - `TWO_CAPTCHA_PROXY` / `TWO_CAPTCHA_PROXY_TYPE` → public upstream proxy (including credentials) so 2Captcha can tunnel through the same IP.
3. **2Captcha parity.** `serpapi_scraper/ai_captcha_bridge.py` now forwards the public proxy, the live browser cookies, and the exact user-agent when submitting jobs. ManualsLib sees matching IPs, sessions, and headers, so the returned tokens remain valid.

## Required Environment Variables

Set the following in `.env` (one block per proxy profile):

```env
# Profile names used by start_with_proxy.py (comma separated)
PROXY_PROFILE_NAMES=proxy_a,proxy_b

# Public upstream proxies (reachable from outside the cluster)
PROXY_A_PUBLIC_URL=http://login:password@proxy-a.example.com:3128
PROXY_A_TYPE=HTTP  # HTTP, HTTPS, SOCKS4, SOCKS5

PROXY_B_PUBLIC_URL=http://login:password@proxy-b.example.com:3128
PROXY_B_TYPE=HTTP
```

The docker-compose file wires each profile to a dedicated Squid container:

```
PROXY_PROXY_A_SQUID_URL=http://squid-proxy-a:8888
PROXY_PROXY_B_SQUID_URL=http://squid-proxy-b:8888
```

Adjust or add additional profiles as needed (e.g., `proxy_c`). When adding a new profile you must:

1. Add its name to `PROXY_PROFILE_NAMES`.
2. Define `PROXY_<NAME>_PUBLIC_URL` and optional `PROXY_<NAME>_TYPE`.
3. Add another Squid service in `docker-compose.yml` that sets `UPSTREAM_PROXY_URLS` to the same public URL.

## How Assignment Works

Compose (or Swarm) automatically names scaled containers `app-1`, `app-2`, `app-3`, and so on. `bin/start_with_proxy.py` grabs the number at the end of the hostname, turns it into a zero-based index, and assigns `profiles[index % len(profiles)]` from `PROXY_PROFILE_NAMES`. With the default `proxy_a,proxy_b` list the pattern becomes:

- `app-1` → `proxy_a`
- `app-2` → `proxy_b`
- `app-3` → `proxy_a`
- `app-4` → `proxy_b`

The script emits `[proxy-bootstrap] hostname=... profile=...` for traceability without leaking credentials.

To skew the ratio, just repeat profile names. Example: `PROXY_PROFILE_NAMES=proxy_a,proxy_a,proxy_a,proxy_b` gives three containers on proxy A for every one on proxy B.

## 2Captcha Requirements

2Captcha expects the following fields when a proxy is used:

| Parameter       | Description                                           |
|-----------------|-------------------------------------------------------|
| `proxytype`     | `HTTP`, `HTTPS`, `SOCKS4`, or `SOCKS5`                |
| `proxy`         | `login:password@host:port` (password optional)        |
| `userAgent`     | Must match `navigator.userAgent` from the Selenium session |
| `cookies`       | Semi-colon separated cookie header (e.g., `PHPSESSID=...; _ga=...`) |
| `data-s`        | Secure token pulled from the page when Google includes it |

`start_with_proxy.py` sets `TWO_CAPTCHA_PROXY`/`TWO_CAPTCHA_PROXY_TYPE` using the chosen profile so `ai_captcha_bridge` can submit jobs with the correct metadata. The bridge also pulls cookies + UA directly from the driver before each submission. Ensure the upstream proxy is reachable from the public internet; 2Captcha workers must be able to connect to it directly.

## Operational Notes

- **Secret hygiene:** Keep credentials in `.env` or your secret manager; do not commit them. Squid logs remain disabled to avoid leaking URLs or tokens.
- **Scaling:** Adjust `deploy.replicas` (or `--scale app=N`) freely. Assignment will stay deterministic as long as container hostnames keep the numeric suffix.
- **Fallback:** Set `CAPTCHA_SOLVER=legacy` if you need to bypass 2Captcha temporarily (e.g., during proxy outages).
- **Monitoring:** Each container exports the selected profile via `CURRENT_PROXY_PROFILE`. Include it in logs/metrics to debug proxy-specific failures without revealing credentials.
