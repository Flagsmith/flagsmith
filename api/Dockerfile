FROM python:3.10-slim as application

WORKDIR /app
COPY . .

# arm architecture platform builds need postgres drivers installing via apt
ARG TARGETARCH
RUN if [ "$TARGETARCH" != "amd64" ]; then apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*; fi;

# Install python dependencies
RUN pip install -r requirements.txt --no-cache-dir --compile

# Compile static Django assets
RUN python manage.py collectstatic --no-input

ARG ACCESS_LOG_LOCATION="/dev/null"
ENV ACCESS_LOG_LOCATION=${ACCESS_LOG_LOCATION}

ENV DJANGO_SETTINGS_MODULE=app.settings.production
EXPOSE 8000

USER nobody

ENTRYPOINT ["./scripts/run-docker.sh"]

# other options below are `migrate` or `serve`
CMD ["migrate-and-serve"]
