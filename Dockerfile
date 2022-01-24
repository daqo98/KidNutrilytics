FROM python:3.8

ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

ARG DEBIAN_FRONTEND=noninteractive
# Microsoft SQL Server Prerequisites
RUN apt-get update \
  && apt-get install -y wget \
  && rm -rf /var/lib/apt/lists/*
RUN wget http://archive.ubuntu.com/ubuntu/pool/main/g/glibc/multiarch-support_2.27-3ubuntu1.4_amd64.deb\
    && apt-get update \
    && apt-get install ./multiarch-support_2.27-3ubuntu1.4_amd64.deb
RUN apt-get update \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/9/prod.list \
        > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    && apt-get -y --no-install-recommends install \
        unixodbc-dev
RUN odbcinst -j
RUN cat /etc/odbcinst.ini
RUN python -m pip install -r requirements.txt
RUN pip install --no-binary=shap 'shap==0.39.0' --force-reinstall
#RUN pip install -U numpy

EXPOSE 8080 2222

CMD python main.py
