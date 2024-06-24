# Your usual Flagsmith release produces of a number of shippable Docker images:

# - Private cloud: API, Unified
# - SaaS: API
# - Open Source: API, Frontend, Unified

# This Dockerfile is meant to build all of the above via composable, interdependent stages.
# The goal is to have as DRY as possible build for all the targets.

# Usage Examples

# Build an Open Source API image:
# $ docker build -t flagsmith-api:dev --target oss-api .

# Build an Open Source Unified image:
# (`oss-unified` stage is the default one, so there's no need to specify a target stage)
# $ docker build -t flagsmith:dev .

# Build a SaaS API image:
# $ GH_TOKEN=$(gh auth token) docker build -t flagsmith-saas-api:dev --target saas-api \
#     --secret="id=sse_pgp_pkey,src=./sse_pgp_pkey.key"\
#     --secret="id=github_private_cloud_token,env=GH_TOKEN" . 

# Build a Private Cloud Unified image:
# $ GH_TOKEN=$(gh auth token) docker build -t flagsmith-private-cloud:dev --target private-cloud-unified \
#     --secret="id=github_private_cloud_token,env=GH_TOKEN" . 

# Table of Contents
# Stages are described as stage-name [dependencies]

# - Intermediary stages
# * build-node [node]
# * build-node-django [build-node]
# * build-node-selfhosted [build-node]
# * build-python [python]
# * build-python-private [build-python]
# * api-runtime [python:slim]
# * api-runtime-private [api-runtime]

# - Target (shippable) stages
# * private-cloud-api [api-runtime-private, build-python-private]
# * private-cloud-unified [api-runtime-private, build-python-private, build-node-django]
# * saas-api [api-runtime-private, build-python-private]
# * oss-api [api-runtime, build-python]
# * oss-frontend [node:slim, build-node-selfhosted]
# * oss-unified [api-runtime, build-python, build-node-django]

ARG CI_COMMIT_SHA=dev

# Pin runtimes versions
ARG NODE_VERSION=16
ARG PYTHON_VERSION=3.11
ARG PYTHON_SITE_DIR=/usr/local/lib/python${PYTHON_VERSION}/site-packages

FROM node:${NODE_VERSION} as node
FROM node:${NODE_VERSION}-slim as node-slim
FROM python:${PYTHON_VERSION} as python
FROM python:${PYTHON_VERSION}-slim as python-slim

# - Intermediary stages
# * build-node
FROM node AS build-node

# Copy the files required to install npm packages
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json frontend/.npmrc ./frontend/.nvmrc ./frontend/
COPY frontend/bin/ ./frontend/bin/
COPY frontend/env/ ./frontend/env/

ARG ENV=selfhosted
RUN cd frontend && ENV=${ENV} npm ci --quiet --production

COPY frontend /app/frontend

# * build-node-django [build-node]
FROM build-node as build-node-django

RUN mkdir /app/api && cd frontend && npm run bundledjango

# * build-node-selfhosted [build-node]
FROM build-node as build-node-selfhosted

RUN cd frontend && npm run bundle

# * build-python
FROM python as build-python
WORKDIR /app

COPY api/pyproject.toml api/poetry.lock api/Makefile ./
ENV POETRY_VIRTUALENVS_CREATE=false POETRY_HOME=/usr/local
RUN make install opts='--without dev'

# * build-python-private [build-python]
FROM build-python AS build-python-private

# Authenticate git with token, install SAML binary dependency,
# private Python dependencies, and integrate private modules
ARG SAML_REVISION
ARG RBAC_REVISION
RUN --mount=type=secret,id=github_private_cloud_token \
  echo "https://$(cat /run/secrets/github_private_cloud_token):@github.com" > ${HOME}/.git-credentials && \
  git config --global credential.helper store && \
  make install-packages opts='--without dev --with saml,auth-controller,ldap,workflows' && \
  make install-private-modules

# * api-runtime
FROM python-slim as api-runtime

ARG TARGETARCH
RUN if [ "${TARGETARCH}" != "amd64" ]; then \
  apt-get update && apt-get install -y libpq-dev && rm -rf /var/lib/apt/lists/*; fi;

WORKDIR /app

COPY api /app/
COPY .release-please-manifest.json /app/.versions.json

ARG ACCESS_LOG_LOCATION="/dev/null"
ENV ACCESS_LOG_LOCATION=${ACCESS_LOG_LOCATION} DJANGO_SETTINGS_MODULE=app.settings.production

ARG CI_COMMIT_SHA
RUN echo ${CI_COMMIT_SHA} > /app/CI_COMMIT_SHA

EXPOSE 8000

ENTRYPOINT ["/app/scripts/run-docker.sh"]

CMD ["migrate-and-serve"]

# * api-runtime-private [api-runtime]
FROM api-runtime as api-runtime-private

# Install SAML binary dependency
RUN apt-get update && apt-get install -y xmlsec1 && rm -rf /var/lib/apt/lists/*

# - Target (shippable) stages
# * private-cloud-api [api-runtime-private, build-python-private]
FROM api-runtime-private as private-cloud-api

ARG PYTHON_SITE_DIR
COPY --from=build-python-private ${PYTHON_SITE_DIR} ${PYTHON_SITE_DIR}
COPY --from=build-python-private /usr/local/bin /usr/local/bin

RUN python manage.py collectstatic --no-input
RUN touch ./ENTERPRISE_VERSION

USER nobody

# * private-cloud-unified [api-runtime-private, build-python-private, build-node-django]
FROM api-runtime-private as private-cloud-unified

ARG PYTHON_SITE_DIR
COPY --from=build-python-private ${PYTHON_SITE_DIR} ${PYTHON_SITE_DIR}
COPY --from=build-python-private /usr/local/bin /usr/local/bin
COPY --from=build-node-django /app/api/static /app/static
COPY --from=build-node-django /app/api/app/templates/webpack /app/app/templates/webpack

RUN python manage.py collectstatic --no-input
RUN touch ./ENTERPRISE_VERSION

USER nobody

# * saas-api [api-runtime-private, build-python-private]
FROM api-runtime-private as saas-api

# Install GnuPG and import private key
RUN --mount=type=secret,id=sse_pgp_pkey \
  apt-get update && apt-get install -y gnupg && \
  gpg --import /run/secrets/sse_pgp_pkey && \
  mv /root/.gnupg/ /app/ && \
  chown -R nobody /app/.gnupg/

ARG PYTHON_SITE_DIR
COPY --from=build-python-private ${PYTHON_SITE_DIR} ${PYTHON_SITE_DIR}
COPY --from=build-python-private /usr/local/bin /usr/local/bin

RUN python manage.py collectstatic --no-input
RUN touch ./SAAS_DEPLOYMENT

USER nobody

# * oss-api [api-runtime, build-python]
FROM api-runtime as oss-api

ARG PYTHON_SITE_DIR
COPY --from=build-python ${PYTHON_SITE_DIR} ${PYTHON_SITE_DIR}
COPY --from=build-python /usr/local/bin /usr/local/bin

RUN python manage.py collectstatic --no-input

USER nobody

# * oss-frontend [build-node-selfhosted]
FROM node-slim AS oss-frontend

USER node
WORKDIR /srv/bt

COPY --from=build-node-selfhosted --chown=node:node /app/frontend .

ENV NODE_ENV=production

ARG CI_COMMIT_SHA
RUN echo ${CI_COMMIT_SHA} > /srv/bt/CI_COMMIT_SHA
COPY .release-please-manifest.json /srv/bt/.versions.json

EXPOSE 8080
CMD ["node",  "./api/index.js"]

# * oss-unified [api-runtime, build-python, build-node-django]
FROM api-runtime as oss-unified

ARG PYTHON_SITE_DIR
COPY --from=build-python ${PYTHON_SITE_DIR} ${PYTHON_SITE_DIR}
COPY --from=build-python /usr/local/bin /usr/local/bin
COPY --from=build-node-django /app/api/static /app/static/
COPY --from=build-node-django /app/api/app/templates/webpack /app/app/templates/webpack

RUN python manage.py collectstatic --no-input

USER nobody
