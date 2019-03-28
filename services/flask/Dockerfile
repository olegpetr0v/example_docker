FROM base/python:3.5
RUN echo Europe/Moscow > /etc/timezone
RUN ln -sf /usr/share/zoneinfo/Europe/Moscow /etc/localtime
RUN mkdir -p /flask
RUN mkdir -p /certs
VOLUME /flask
VOLUME /certs
WORKDIR /flask
USER root
CMD gunicorn -c flask.conf run:app
