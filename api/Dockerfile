# NOTE: Why not Alpine? Because Alpine demands installation of OS software
# prior to running app code, which leads to maintenance work and a larger image
# size compared to Debian — considering Debian layers are shared across images.
FROM python:3.12

# Prevent Python from buffering stdout and stderr
# https://docs.python.org/3/using/cmdline.html#envvar-PYTHONUNBUFFERED
ENV PYTHONUNBUFFERED=1

# Prevent Python from writing .pyc files to disk
# https://docs.python.org/3/using/cmdline.html#envvar-PYTHONDONTWRITEBYTECODE
ENV PYTHONDONTWRITEBYTECODE=1

# Install Python packages
WORKDIR /tmp
ARG POETRY_VERSION_CONSTRAINT
ARG INSTALL_DEV_DEPENDENCIES
COPY api/pyproject.toml api/poetry.lock ./
RUN \
    pip install -q poetry${POETRY_VERSION_CONSTRAINT:-} &&\
    poetry config virtualenvs.create false &&\
    poetry config cache-dir /var/cache/pypoetry &&\
    ###
    # NOTE: Forcefully delete optional private dependencies for now since
    # Poetry needs to fetch them in order to calculate the dependency tree. See
    # https://github.com/python-poetry/poetry/issues/4562
    # TODO: Improve management of enterprise features
    sed -ie '/tool.poetry.group.auth-controller/,+1d' pyproject.toml &&\
    sed -ie '/tool.poetry.group.saml/,+1d' pyproject.toml &&\
    sed -ie '/tool.poetry.group.ldap/,+1d' pyproject.toml &&\
    sed -ie '/tool.poetry.group.workflows/,+1d' pyproject.toml &&\
    sed -ie '/tool.poetry.group.licensing/,+1d' pyproject.toml &&\
    poetry lock &&\
    ###
    poetry install --no-root $([ "$INSTALL_DEV_DEPENDENCIES" != "true" ] && echo "--without dev") &&\
    rm -rf /var/cache/pypoetry &&\
    rm -rf /tmp/*

# Prepare the app
WORKDIR /opt/app
COPY api/ .
EXPOSE 8000
CMD ["flagsmith", "start", "api"]
