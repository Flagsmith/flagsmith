#!/usr/bin/env bash
# Make sure the services the suite needs are up and healthy, cheaply.
#
# `docker compose up --wait` is the correct thing to run, but it spends about
# two seconds converging the project -- inspecting every container and
# recomputing config hashes -- even when there is nothing to do, and that is a
# large slice of a focused `make test`. Reading the healthcheck verdict Docker
# already has costs about a tenth of that and answers the same question in the
# overwhelmingly common case where the stack is up, so try that first and fall
# back to Compose.
#
# Readiness is taken from the healthchecks rather than by opening a socket:
# Docker publishes a port the moment a container starts, roughly half a second
# before PostgreSQL will accept a query, and pytest connects immediately.
set -euo pipefail

project="${COMPOSE_PROJECT_NAME:-flagsmith}"

# The services `make test` talks to. Each one needs a healthcheck in
# docker-compose.local.yml, or it can never be seen as ready.
required=(test-db clickhouse)

# Pull "host port" out of a URL like postgresql://user:pw@host:5432/name.
endpoint_of() {
  sed -E 's#^[^:]+://([^@]*@)?([^:/]+):([0-9]+).*$#\2 \3#' <<<"$1"
}

# Where a service is reached when this project does not own it -- in CI, say,
# where the services are managed for us and there is no container to inspect.
external_endpoint_of() {
  case "$1" in
  test-db) endpoint_of "${TEST_DATABASE_URL:-${DATABASE_URL:-}}" ;;
  clickhouse) printf '%s %s' "${CLICKHOUSE_HOST:-localhost}" "${CLICKHOUSE_PORT:-9000}" ;;
  esac
}

# Bash's /dev/tcp needs no subprocess, unlike nc(1), which is not everywhere.
reachable() {
  (exec 3<>"/dev/tcp/$1/$2") 2>/dev/null
}

converge() {
  exec docker compose up --remove-orphans --wait -d
}

# One `docker ps` for the whole project: a label filter keeps it to about 80ms,
# where the equivalent through Compose costs a couple of seconds. `Status`
# carries the healthcheck verdict, as in "Up 5 minutes (healthy)".
containers=$(
  docker ps --all --filter "label=com.docker.compose.project=${project}" \
    --format '{{.Label "com.docker.compose.service"}} {{.Status}}'
) || converge

for service in "${required[@]}"; do
  status=$(grep "^${service} " <<<"${containers}" || true)

  if [[ -z ${status} ]]; then
    # No container, so the endpoint is managed outside this project. A socket
    # is all we can check, and whoever is managing it owns its readiness.
    endpoint=$(external_endpoint_of "${service}")
    if [[ -z ${endpoint} ]]; then
      echo "ensure-services: ${service} has no container in project" \
        "'${project}' and no endpoint configured; is your .env-local missing?" >&2
      exit 1
    fi
    # shellcheck disable=SC2086 # deliberate split into host and port
    reachable ${endpoint} || converge
    continue
  fi

  [[ ${status} == *"(healthy)"* ]] || converge
done
