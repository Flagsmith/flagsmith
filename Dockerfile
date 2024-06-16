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
# $ docker build -t flagsmith-saas-api:dev --target saas-api \
#     --secret="id=sse_pgp_pkey,src=/etc/sse_pgp_key"\
#     --secret="id=github_private_cloud_token,src=/etc/github_private_cloud_token" . 

# Build a Private Cloud Unified image:
# $ docker build -t flagsmith-private-cloud:dev --target private-cloud-unified \
#     --secret="id=github_private_cloud_token,src=/etc/github_private_cloud_token" . 

# Table of Contents
# Stages are described as stage-name [dependencies]

# - Intermediary stages
# * build-node [node]
# * build-node-django [build-node]
# * build-node-selfhosted [build-node]
# * build-python [python]
# * build-python-private [build-python]
# * api-runtime [python:slim]

# - Target (shippable) stages
# * private-cloud-api [api-runtime, build-python-private]
# * private-cloud-unified [api-runtime, build-python-private, build-node-django]
# * saas-api [api-runtime, build-python-private]
# * oss-api [api-runtime, build-python]
# * oss-frontend [node:slim, build-node-selfhosted]
# * oss-unified [api-runtime, build-python, build-node-django]

ARG CI_COMMIT_SHA=dev

# - Intermediary stages
# * build-node
FROM node:16 AS build-node

# Copy the files required to install npm packages
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json frontend/.npmrc ./frontend/.nvmrc ./frontend/
COPY frontend/bin/ ./frontend/bin/
COPY frontend/env/ ./frontend/env/

# since ENV is only used for the purposes of copying the correct
# project_${env}.js file to common/project.js, this is a build arg
# which subsequently gets set as an environment variable. This is
# done to avoid confusion since it is not a required run time var.
ARG ENV=selfhosted
RUN cd frontend && ENV=${ENV} npm ci --quiet --production

COPY frontend /app/frontend

# * build-node-django [build-node]
FROM build-node as build-node-django

RUN mkdir /app/api
ENV STATIC_ASSET_CDN_URL=/static/
RUN cd frontend && npm run bundledjango

# * build-node-selfhosted [build-node]
FROM build-node as build-node-selfhosted

RUN cd frontend && npm run bundle

# * build-python
FROM python:3.11 as build-python
WORKDIR /app

COPY api/pyproject.toml api/poetry.lock api/Makefile ./
ENV POETRY_VIRTUALENVS_CREATE=false
ENV POETRY_HOME=/usr/local
RUN make install opts='--without dev'

# * build-python-private [build-python]
FROM build-python AS build-python-private

# Authenticate git with token to install private packages
RUN --mount=type=secret,id=github_private_cloud_token \
  echo "https://$(cat /run/secrets/github_private_cloud_token):@github.com" > ${HOME}/.git-credentials && \
  git config --global credential.helper store

# Install SAML binary dependency
RUN apt-get update && apt-get install -y xmlsec1

# Install private Python dependencies
RUN make install-packages opts='--without dev --with saml,auth-controller,ldap,workflows'

# Integrate private modules
ARG SAML_REVISION
ARG AUTH_CONTROLLER_REVISION
ARG RBAC_REVISION
RUN make install-private-modules

# * api-runtime
FROM python:3.11-slim as api-runtime

WORKDIR /app

COPY api /app/
COPY .release-please-manifest.json /app/.versions.json

ARG ACCESS_LOG_LOCATION="/dev/null"
ENV ACCESS_LOG_LOCATION=${ACCESS_LOG_LOCATION}
ENV DJANGO_SETTINGS_MODULE=app.settings.production

RUN echo ${CI_COMMIT_SHA} > /app/CI_COMMIT_SHA

EXPOSE 8000

ENTRYPOINT ["/app/scripts/run-docker.sh"]

# other options below are `migrate` or `serve`
CMD ["migrate-and-serve"]

# - Target (shippable) stages
# * private-cloud-api [api-runtime, build-python-private]
FROM api-runtime as private-cloud-api

COPY --from=build-python-private /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=build-python-private /usr/local/bin /usr/local/bin

RUN python manage.py collectstatic --no-input
RUN touch ./ENTERPRISE_VERSION

USER nobody

# * private-cloud-unified [api-runtime, build-python-private, build-node-django]
FROM api-runtime as private-cloud-unified

COPY --from=build-node-django /app/api/static /app/static
COPY --from=build-node-django /app/api/app/templates/webpack /app/app/templates/webpack
COPY --from=build-python-private /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=build-python-private /usr/local/bin /usr/local/bin

RUN python manage.py collectstatic --no-input
RUN touch ./ENTERPRISE_VERSION

USER nobody

# * saas-api [api-runtime, build-python-private]
FROM api-runtime as saas-api

# Install GnuPG and import private key
RUN --mount=type=secret,id=sse_pgp_pkey \
  apt-get update && apt-get install -y gnupg && \
  gpg --import /run/secrets/sse_pgp_pkey && \
  mv /root/.gnupg /app/; \
  chown -R nobody /app/.gnupg

COPY --from=build-python-private /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=build-python-private /usr/local/bin /usr/local/bin

RUN python manage.py collectstatic --no-input
RUN touch ./SAAS_DEPLOYMENT

USER nobody

# * oss-api [api-runtime, build-python]
FROM api-runtime as oss-api

COPY --from=build-python /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=build-python /usr/local/bin /usr/local/bin

RUN python manage.py collectstatic --no-input

USER nobody

# * oss-frontend [build-node-selfhosted]
FROM node:16-slim AS oss-frontend

USER node
WORKDIR /srv/bt

COPY --from=build-node-selfhosted --chown=node:node /app/frontend .

ENV NODE_ENV=production

RUN echo ${CI_COMMIT_SHA} > /srv/bt/CI_COMMIT_SHA
COPY .release-please-manifest.json /srv/bt/.versions.json

EXPOSE 8080
CMD ["node",  "./api/index.js"]

# * oss-unified [build-python, build-node-django]
FROM api-runtime as oss-unified

COPY --from=build-node-django /app/api/static /app/static/
COPY --from=build-node-django /app/api/app/templates/webpack /app/app/templates/webpack
COPY --from=build-python /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=build-python /usr/local/bin /usr/local/bin

RUN python manage.py collectstatic --no-input

USER nobody
