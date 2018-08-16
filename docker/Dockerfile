FROM python:2.7

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
    && rm -rf /var/lib/apt/lists/*

RUN pip install pipenv

WORKDIR /usr/src/app
COPY Pipfile* ./
RUN pipenv install --system --deploy
COPY src/ .

ENV DJANGO_SETTINGS_MODULE=app.settings.master-docker

EXPOSE 8000
