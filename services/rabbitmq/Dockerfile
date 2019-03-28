FROM base/rabbitmq:3-management
RUN echo Europe/Moscow > /etc/timezone
RUN ln -sf /usr/share/zoneinfo/Europe/Moscow /etc/localtime
VOLUME /var/lib/rabbitmq
USER root
