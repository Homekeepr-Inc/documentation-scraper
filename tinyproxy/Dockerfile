FROM alpine:latest

RUN apk add --no-cache tinyproxy gettext

COPY tinyproxy.conf.template /etc/tinyproxy/tinyproxy.conf.template

EXPOSE 8888

CMD envsubst < /etc/tinyproxy/tinyproxy.conf.template > /etc/tinyproxy/tinyproxy.conf && tinyproxy -d