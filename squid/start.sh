#!/bin/sh
set -euo pipefail

if [ -z "${UPSTREAM_PROXY_URLS:-}" ]; then
    echo "UPSTREAM_PROXY_URLS must be set (comma-separated list of proxy URLs)" >&2
    exit 1
fi

CACHE_PEER_CONFIG="$(/app/squid/render_cache_peer.py)"
export CACHE_PEER_CONFIG

envsubst '$CACHE_PEER_CONFIG' < /etc/squid/squid.conf.template > /etc/squid/squid.conf

# Clean up stale pid file from any unclean shutdown
rm -f /var/run/squid.pid

squid -f /etc/squid/squid.conf -N
