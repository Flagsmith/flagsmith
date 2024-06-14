# Step 1 - Build Front End Application
FROM node:16 AS build-frontend

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

# Copy the entire project - Webpack puts compiled assets into the Django folder
COPY . .
ENV STATIC_ASSET_CDN_URL=/static/
RUN cd frontend && npm run bundledjango

# Step 2 - Build Python virtualenv
FROM python:3.11 as build-python
WORKDIR /app

COPY api/pyproject.toml api/poetry.lock api/Makefile ./
ARG POETRY_VIRTUALENVS_CREATE=false
RUN make install-poetry
ENV PATH="$PATH:/root/.local/bin"

RUN --mount=type=secret,id=github_private_access_token \
  if [ -f /run/secrets/github_private_access_token ]; then \
  echo "https://$(cat /run/secrets/github_private_access_token):@github.com" > ${HOME}/.git-credentials && \
  git-config --global credential.helper store; fi

ARG POETRY_OPTS
RUN make install-packages opts="${POETRY_OPTS}"

ARG PRIVATE_CLOUD="0"
ENV GIT_TERMINAL_PROMPT="0"

# Install SAML binary dependency if required and integrate SAML module
ARG SAML_REVISION=v1.6.0
RUN if [ "${PRIVATE_CLOUD}" = "1" ]; \
  then apt-get update && apt-get install -y xmlsec1 && \
  git clone https://github.com/flagsmith/flagsmith-saml --depth 1 --branch ${SAML_REVISION} && \
  mv ./flagsmith-saml/saml /usr/local/lib/python3.11/site-packages; fi;

# Integrate Auth Controller module if required
ARG AUTH_CONTROLLER_REVISION=v0.0.1
RUN if [ "${PRIVATE_CLOUD}" = "1" ]; \
  then git clone https://github.com/flagsmith/flagsmith-auth-controller --depth 1 --branch ${AUTH_CONTROLLER_REVISION} && \
  mv ./flagsmith-auth-controller/auth_controller /usr/local/lib/python3.11/site-packages; fi;

# Integrate RBAC module if required
ARG RBAC_REVISION=v0.7.0
RUN if [ "${PRIVATE_CLOUD}" = "1" ]; \
  then git clone https://github.com/flagsmith/flagsmith-rbac --depth 1 --branch ${RBAC_REVISION} && \
  mv ./flagsmith-rbac/rbac /usr/local/lib/python3.11/site-packages; fi;

# Step 3 - Build Django Application
FROM python:3.11-slim as application
WORKDIR /app

# arm architecture platform builds need postgres drivers installing via apt
ARG TARGETARCH
RUN if [ "${TARGETARCH}" != "amd64" ]; then apt-get update && apt-get install -y libpq-dev && rm -rf /var/lib/apt/lists/*; fi;

# Copy the python venv from step 2
COPY --from=build-python /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
# Copy the bin folder as well to copy the executables created in package installation
COPY --from=build-python /usr/local/bin /usr/local/bin

COPY api /app/
COPY .release-please-manifest.json /app/.versions.json

# Compile static Django assets
RUN python /app/manage.py collectstatic --no-input

# Copy the compiled front end assets from the previous build step
COPY --from=build-frontend /app/api/static /app/static/
COPY --from=build-frontend /app/api/app/templates/webpack /app/app/templates/webpack

ARG ACCESS_LOG_LOCATION="/dev/null"
ENV ACCESS_LOG_LOCATION=${ACCESS_LOG_LOCATION}
ENV DJANGO_SETTINGS_MODULE=app.settings.production

ARG CI_COMMIT_SHA=dev
RUN echo ${CI_COMMIT_SHA} > ./CI_COMMIT_SHA
ARG SHIP_REASON=DEVELOPMENT
RUN touch ./${SHIP_REASON}

EXPOSE 8000

USER nobody

ENTRYPOINT ["./scripts/run-docker.sh"]

# other options below are `migrate` or `serve`
CMD ["migrate-and-serve"]
