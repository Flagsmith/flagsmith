FROM python:3.8-slim as application

WORKDIR /app

# Install python packages locally in a virtualenv
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY requirements.txt /app/
RUN apt-get update \
    && apt-get install -y git \
    && pip install -r requirements.txt --no-cache-dir --compile \
    && rm -rf /var/lib/apt/lists/*

COPY . /app/

RUN python manage.py collectstatic --no-input

ARG ACCESS_LOG_LOCATION="/dev/null"
ENV ACCESS_LOG_LOCATION=${ACCESS_LOG_LOCATION}

ENV DJANGO_SETTINGS_MODULE=app.settings.production
EXPOSE 8000

USER nobody

CMD ["./scripts/run-docker.sh"]
