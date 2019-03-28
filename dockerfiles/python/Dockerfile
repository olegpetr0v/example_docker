
FROM python:3.5-slim
RUN apt-get update
RUN apt-get install -y mc nano
RUN pip install --upgrade pip
RUN pip install pika
RUN pip install psycopg2-binary pymssql pymysql
RUN pip install requests requests_ntlm
RUN pip install flask gunicorn flask_httpauth
RUN pip install --upgrade setuptools
RUN pip install paramiko scp
RUN pip install tzlocal pytz
