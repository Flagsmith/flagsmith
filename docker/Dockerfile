FROM python:2.7

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app
COPY requirements-docker.txt ./
RUN pip install -r requirements-docker.txt
COPY src/ .

ENV DJANGO_SETTINGS_MODULE=app.settings.master-docker

EXPOSE 8000
