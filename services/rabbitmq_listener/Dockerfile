FROM base/python:3.5
RUN echo Europe/Moscow > /etc/timezone
RUN ln -sf /usr/share/zoneinfo/Europe/Moscow /etc/localtime
RUN mkdir -p /rabbitmq_listener
VOLUME /rabbitmq_listener
WORKDIR /
USER root
CMD python /rabbitmq_listener/rabbitmq_listener.py
