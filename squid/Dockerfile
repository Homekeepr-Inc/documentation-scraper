FROM alpine:latest

RUN apk add --no-cache squid gettext

COPY squid.conf.template /etc/squid/squid.conf.template

EXPOSE 8888

CMD envsubst < /etc/squid/squid.conf.template > /etc/squid/squid.conf && \
    echo "--- Generated squid.conf ---" && \
    cat /etc/squid/squid.conf && \
    echo "--- End Generated squid.conf ---" && \
    squid -f /etc/squid/squid.conf -N
