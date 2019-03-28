FROM centos:7
RUN yum -y install wget mc nano bzip2 which
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-4.5.11-Linux-x86_64.sh
RUN bash Miniconda3-4.5.11-Linux-x86_64.sh -b -p /miniconda3
RUN echo "# added by Miniconda3 installer" >> /root/.bashrc
RUN echo "export PATH="/miniconda3/bin:$PATH"" >> /root/.bashrc
ENV PATH="/miniconda3/bin:$PATH"
RUN conda install -c conda-forge jupyterhub notebook
RUN pip install --upgrade pip
RUN pip install pika psycopg2-binary pytz pymssql pymysql requests requests_ntlm
RUN pip install flask gunicorn flask_httpauth
RUN pip install --upgrade setuptools
RUN pip install paramiko scp
RUN pip install tzlocal

