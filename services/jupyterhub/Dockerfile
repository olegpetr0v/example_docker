FROM base/jupyterhub:3.7
RUN echo Europe/Moscow > /etc/timezone
RUN ln -sf /usr/share/zoneinfo/Europe/Moscow /etc/localtime

RUN mkdir -p /services/flask
RUN mkdir -p /services/certs
RUN mkdir -p /services/nginx
RUN mkdir -p /services/rabbitmq_listener
RUN mkdir -p /services/db_loader

VOLUME /services/flask
VOLUME /services/certs
VOLUME /services/nginx
VOLUME /services/rabbitmq_listener
VOLUME /services/db_loader

VOLUME /home
USER root
CMD jupyterhub --ip 172.20.0.12 --port 8000
