# Flagsmith MCP server image.
#
# To build locally from the repo root:
# $ docker build -f mcp/Dockerfile -t flagsmith-mcp:dev .

ARG CI_COMMIT_SHA=dev

# Pin runtimes versions
ARG PYTHON_VERSION=3.13
ARG UV_VERSION=0.11.18

FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv
FROM cgr.dev/chainguard/wolfi-base:latest AS wolfi-base

# * build [wolfi-base]
FROM wolfi-base AS build
WORKDIR /build

ARG PYTHON_VERSION
RUN apk add build-base \
  python-${PYTHON_VERSION} \
  python-${PYTHON_VERSION}-dev

COPY --from=uv /uv /usr/local/bin/uv

ENV UV_PROJECT_ENVIRONMENT=/build/.venv \
  UV_PYTHON_PREFERENCE=only-system \
  UV_PYTHON=python${PYTHON_VERSION} \
  UV_LINK_MODE=copy \
  UV_COMPILE_BYTECODE=1 \
  UV_CACHE_DIR=/root/.cache/uv

# Resolve dependencies first so the layer is cached independently of source changes.
COPY mcp/pyproject.toml mcp/uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --frozen --no-dev --no-install-project

# Install the project itself as a non-editable wheel into the venv.
COPY mcp/README.md ./
COPY mcp/src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
  uv sync --frozen --no-dev --no-editable

# * runtime [wolfi-base]
FROM wolfi-base AS runtime

# Install Python and make it available to the venv's entrypoints.
ARG PYTHON_VERSION
RUN apk add python-${PYTHON_VERSION} && \
  mkdir /build/ && ln -s /usr/local/ /build/.venv

COPY --from=build /build/.venv/ /usr/local/

ARG CI_COMMIT_SHA
RUN echo ${CI_COMMIT_SHA} > /CI_COMMIT_SHA

ENV TRANSPORT=http \
  FASTMCP_HOST=0.0.0.0 \
  FASTMCP_PORT=8000

EXPOSE 8000

USER nobody

ENTRYPOINT ["flagsmith-mcp"]

HEALTHCHECK --interval=10s --timeout=3s --retries=3 --start-period=10s \
  CMD ["python", "-c", "import os,urllib.request; urllib.request.urlopen(f\"http://127.0.0.1:{os.environ['FASTMCP_PORT']}/health\", timeout=2)"]
