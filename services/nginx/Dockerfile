FROM base/nginx:1.15
RUN echo Europe/Moscow > /etc/timezone
RUN ln -sf /usr/share/zoneinfo/Europe/Moscow /etc/localtime
VOLUME /etc/nginx/conf.d
USER root
