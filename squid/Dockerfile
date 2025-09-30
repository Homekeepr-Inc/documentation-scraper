FROM alpine:latest

RUN apk add --no-cache squid gettext

COPY squid.conf.template /etc/squid/squid.conf.template
COPY start.sh /start.sh
RUN chmod +x /start.sh

EXPOSE 8888

CMD ["/start.sh"]