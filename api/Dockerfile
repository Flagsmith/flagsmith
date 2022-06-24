FROM python:3.10-slim as application

# arm architecture platform builds need postgres drivers installing via apt
# by default we want to build amd64 arch images
ARG TARGETARCH
RUN if [ "${TARGETARCH}" != "amd64" ]; then apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*; fi;

# Install re2
ARG GOOGLE_RE2_VERSION="0.2.20220601"
ARG TARGETPLATFORM
RUN pip install google-re2==${GOOGLE_RE2_VERSION}

WORKDIR /app
COPY . .

# pysaml2 dependency
RUN apt update && apt install -y xmlsec1

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
