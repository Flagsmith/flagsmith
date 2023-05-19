# Step 1 - Build Front End Application
FROM node:16 AS build-frontend

# Copy the entire project - Webpack puts compiled assets into the Django folder
WORKDIR /app
COPY . .

RUN cd frontend && npm ci --quiet --production
ENV ENV=prod
ENV STATIC_ASSET_CDN_URL=/static/
RUN cd frontend && npm run bundledjango


# Step 2 - Build Python virtualenv
FROM python:3.11 as build-python
WORKDIR /app

RUN apt-get update && apt-get install -y gcc build-essential libpq-dev musl-dev python3-dev

ENV POETRY_VERSION=1.5.0

RUN pip install --upgrade pip
RUN pip install --upgrade setuptools
RUN pip install "poetry==$POETRY_VERSION"

# Set up venv
RUN python -m venv /opt/venv

COPY api/pyproject.toml api/poetry.lock ./
RUN . /opt/venv/bin/activate && poetry install --only main

# Step 2 - Build Django Application
FROM python:3.11-slim as application

WORKDIR /app
COPY api /app/

# Install SAML dependency if required
ARG SAML_INSTALLED="0"
RUN if [ "${SAML_INSTALLED}" = "1" ]; then apt-get update && apt-get install -y xmlsec1; fi;

# arm architecture platform builds need postgres drivers installing via apt
ARG TARGETARCH
RUN if [ "${TARGETARCH}" != "amd64" ]; then apt-get update && apt-get install -y libpq-dev && rm -rf /var/lib/apt/lists/*; fi;

# Copy the python venv from step 2
COPY --from=build-python /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Compile static Django assets
RUN python /app/manage.py collectstatic --no-input

# Copy the compiled front end assets from the previous build step
COPY --from=build-frontend /app/api/static /app/static/
COPY --from=build-frontend /app/api/app/templates/webpack /app/app/templates/webpack

ARG ACCESS_LOG_LOCATION="/dev/null"
ENV ACCESS_LOG_LOCATION=${ACCESS_LOG_LOCATION}
ENV DJANGO_SETTINGS_MODULE=app.settings.production

EXPOSE 8000

USER nobody

ENTRYPOINT ["./scripts/run-docker.sh"]

# other options below are `migrate` or `serve`
CMD ["migrate-and-serve"]
