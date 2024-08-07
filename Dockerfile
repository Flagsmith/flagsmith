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
# * build-python [wolfi-base]
# * build-python-private [build-python]
# * api-runtime [wolfi-base]
# * api-runtime-private [api-runtime]

# - Internal stages
# * api-test [build-python]

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

FROM public.ecr.aws/docker/library/node:${NODE_VERSION}-bookworm as node
FROM cgr.dev/chainguard/wolfi-base:latest as wolfi-base

# - Intermediary stages
# * build-node
FROM node AS build-node

# Copy the files required to install npm packages
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json frontend/.npmrc ./frontend/.nvmrc ./frontend/
COPY frontend/bin/ ./frontend/bin/
COPY frontend/env/ ./frontend/env/

ARG ENV=selfhosted
RUN cd frontend && ENV=${ENV} npm ci --quiet --production

COPY frontend /build/frontend

# * build-node-django [build-node]
FROM build-node as build-node-django

RUN mkdir /build/api && cd frontend && npm run bundledjango

# * build-node-selfhosted [build-node]
FROM build-node as build-node-selfhosted

RUN cd frontend && npm run bundle

# * build-python
FROM wolfi-base as build-python
WORKDIR /build

ARG PYTHON_VERSION
RUN apk add build-base linux-headers curl git \
  python-${PYTHON_VERSION} \
  python-${PYTHON_VERSION}-dev \
  py${PYTHON_VERSION}-pip 

COPY api/pyproject.toml api/poetry.lock api/Makefile ./
ENV POETRY_VIRTUALENVS_IN_PROJECT=true \
  POETRY_VIRTUALENVS_OPTIONS_ALWAYS_COPY=true \
  POETRY_VIRTUALENVS_OPTIONS_NO_PIP=true \
  POETRY_VIRTUALENVS_OPTIONS_NO_SETUPTOOLS=true \
  POETRY_HOME=/opt/poetry \
  PATH="/opt/poetry/bin:$PATH"
RUN make install opts='--without dev'

# * build-python-private [build-python]
FROM build-python AS build-python-private

# Authenticate git with token, install private Python dependencies,
# and integrate private modules
ARG SAML_REVISION
ARG RBAC_REVISION
RUN --mount=type=secret,id=github_private_cloud_token \
  echo "https://$(cat /run/secrets/github_private_cloud_token):@github.com" > ${HOME}/.git-credentials && \
  git config --global credential.helper store && \
  make install-packages opts='--without dev --with saml,auth-controller,ldap,workflows' && \
  make install-private-modules

# * api-runtime
FROM wolfi-base as api-runtime

# Install Python and make it available to venv entrypoints
ARG PYTHON_VERSION
RUN apk add python-${PYTHON_VERSION} && \
  mkdir /build/ && ln -s /usr/local/ /build/.venv

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
RUN apk add xmlsec

# - Internal stages
# * api-test [build-python]
FROM build-python AS api-test

RUN make install-packages opts='--with dev'

WORKDIR /app

COPY api /app/

CMD ["make test"]

# - Target (shippable) stages
# * private-cloud-api [api-runtime-private, build-python-private]
FROM api-runtime-private as private-cloud-api

COPY --from=build-python-private /build/.venv/ /usr/local/

RUN python manage.py collectstatic --no-input
RUN touch ./ENTERPRISE_VERSION

USER nobody

# * private-cloud-unified [api-runtime-private, build-python-private, build-node-django]
FROM api-runtime-private as private-cloud-unified

COPY --from=build-python-private /build/.venv/ /usr/local/
COPY --from=build-node-django /build/api/ /app/

RUN python manage.py collectstatic --no-input
RUN touch ./ENTERPRISE_VERSION

USER nobody

# * saas-api [api-runtime-private, build-python-private]
FROM api-runtime-private as saas-api

# Install GnuPG and import private key
RUN --mount=type=secret,id=sse_pgp_pkey \
  apk add gpg gpg-agent && \
  gpg --import /run/secrets/sse_pgp_pkey && \
  mv /root/.gnupg/ /app/ && \
  chown -R nobody /app/.gnupg/

COPY --from=build-python-private /build/.venv/ /usr/local/

RUN python manage.py collectstatic --no-input
RUN touch ./SAAS_DEPLOYMENT

USER nobody

# * oss-api [api-runtime, build-python]
FROM api-runtime as oss-api

COPY --from=build-python /build/.venv/ /usr/local/

RUN python manage.py collectstatic --no-input

USER nobody

# * oss-frontend [build-node-selfhosted]
FROM wolfi-base AS oss-frontend

ARG NODE_VERSION
RUN apk add nodejs-${NODE_VERSION}

WORKDIR /srv/bt

COPY --from=build-node-selfhosted /build/frontend/ /srv/bt/

ENV NODE_ENV=production

ARG CI_COMMIT_SHA
RUN echo ${CI_COMMIT_SHA} > /srv/bt/CI_COMMIT_SHA
COPY .release-please-manifest.json /srv/bt/.versions.json

EXPOSE 8080

CMD ["node",  "./api/index.js"]

USER nobody

# * oss-unified [api-runtime, build-python, build-node-django]
FROM api-runtime as oss-unified

COPY --from=build-python /build/.venv/ /usr/local/
COPY --from=build-node-django /build/api/ /app/

RUN python manage.py collectstatic --no-input

USER nobody
