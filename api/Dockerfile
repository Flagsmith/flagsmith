
# Step 1 - Build Python virtualenv
FROM python:3.11 as build-python
WORKDIR /app

COPY pyproject.toml poetry.lock Makefile ./

ARG POETRY_VIRTUALENVS_CREATE=false
RUN make install-poetry
ENV PATH="$PATH:/root/.local/bin"

RUN make install-packages opts="--no-root --only main"

# Step 2 - Build Django Application
FROM python:3.11-slim as application
WORKDIR /app

# Install SAML dependency if required
ARG SAML_INSTALLED="0"
RUN if [ "${SAML_INSTALLED}" = "1" ]; then apt-get update && apt-get install -y xmlsec1; fi;

# arm architecture platform builds need postgres drivers installing via apt
ARG TARGETARCH
RUN if [ "${TARGETARCH}" != "amd64" ]; then apt-get update && apt-get install -y libpq-dev && rm -rf /var/lib/apt/lists/*; fi;

# Copy the python venv from step 2
COPY --from=build-python /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
# Copy the bin folder as well to copy the executables created in package installation
COPY --from=build-python /usr/local/bin /usr/local/bin

COPY . .

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
