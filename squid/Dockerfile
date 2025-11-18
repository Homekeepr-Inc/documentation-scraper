FROM alpine:latest

RUN apk add --no-cache squid gettext python3

WORKDIR /app/squid

COPY squid.conf.template /etc/squid/squid.conf.template
COPY start.sh render_cache_peer.py ./

RUN chmod +x /app/squid/start.sh /app/squid/render_cache_peer.py

EXPOSE 8888

ENTRYPOINT ["/app/squid/start.sh"]
