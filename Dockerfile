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
FROM python:3.12 as build-python
WORKDIR /app

COPY api/pyproject.toml api/poetry.lock api/Makefile ./
ARG POETRY_VIRTUALENVS_CREATE=false
RUN make install-poetry
ENV PATH="$PATH:/root/.local/bin"

ARG GH_TOKEN
RUN if [ -n "${GH_TOKEN}" ]; \
  then echo "https://${GH_TOKEN}:@github.com" > ${HOME}/.git-credentials \
  && git config --global credential.helper store; fi;

ARG POETRY_OPTS
RUN make install-packages opts="${POETRY_OPTS}"

# Step 3 - Build Django Application
FROM python:3.12-slim as application
WORKDIR /app

# Install SAML dependency if required
ARG SAML_INSTALLED="0"
RUN if [ "${SAML_INSTALLED}" = "1" ]; then apt-get update && apt-get install -y xmlsec1; fi;

# arm architecture platform builds need postgres drivers installing via apt
ARG TARGETARCH
RUN if [ "${TARGETARCH}" != "amd64" ]; then apt-get update && apt-get install -y libpq-dev && rm -rf /var/lib/apt/lists/*; fi;

# Copy the python venv from step 2
COPY --from=build-python /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
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

EXPOSE 8000

USER nobody

ENTRYPOINT ["./scripts/run-docker.sh"]

# other options below are `migrate` or `serve`
CMD ["migrate-and-serve"]
