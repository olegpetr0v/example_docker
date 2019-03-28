FROM base/python:3.5
RUN echo Europe/Moscow > /etc/timezone
RUN ln -sf /usr/share/zoneinfo/Europe/Moscow /etc/localtime
RUN mkdir -p /db_loader
RUN mkdir -p /rabbitmq_listener
VOLUME /db_loader
VOLUME /rabbitmq_listener
WORKDIR /
USER root
CMD python /db_loader/db_loader.py
