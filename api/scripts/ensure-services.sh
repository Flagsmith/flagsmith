#!/usr/bin/env bash
# A faster alternative to `docker compose up --wait` (around ~0.15s vs ~2s on average).
set -euo pipefail

project="${COMPOSE_PROJECT_NAME:-flagsmith}"

# Pull "host port" out of a URL like postgresql://user:pw@host:5432/name.
endpoint_of() {
  sed -E 's#^[^:]+://([^@]*@)?([^:/]+):([0-9]+).*$#\2 \3#' <<<"$1"
}

# The endpoints the suite connects to. Checking these rather than a list of
# service names keeps the check honest wherever they point: `.env-local` sends
# both databases to `test-db`, `.env-ci` sends them to `db` and `analytics-db`.
endpoints=$(
  {
    endpoint_of "${TEST_DATABASE_URL:-${DATABASE_URL:-}}"
    endpoint_of "${TEST_ANALYTICS_DATABASE_URL:-${ANALYTICS_DATABASE_URL:-}}"
    printf '%s %s\n' "${CLICKHOUSE_HOST:-localhost}" "${CLICKHOUSE_PORT:-9000}"
  } | sort -u
)

# Bash's /dev/tcp needs no subprocess, unlike nc(1), which is not everywhere.
reachable() {
  (exec 3<>"/dev/tcp/$1/$2") 2>/dev/null
}

compose_fallback() {
  exec docker compose up --remove-orphans --wait -d
}

# One `docker ps` for the whole project: a label filter keeps it to about 80ms,
# where the equivalent through Compose costs a couple of seconds. `Status`
# carries the healthcheck verdict, as in "Up 5 minutes (healthy)", and `Ports`
# the published port, as in "0.0.0.0:5434->5432/tcp".
containers=$(
  docker ps --filter "label=com.docker.compose.project=${project}" \
    --format '{{.Ports}} {{.Status}}'
) || compose_fallback

while read -r host port; do
  container=$(grep ":${port}->" <<<"${containers}" || true)

  if [[ -z ${container} ]]; then
    # Nothing in this project publishes that port, so the service is managed
    # from outside it and whoever manages it owns its readiness. A stopped
    # container looks the same, and the socket check sends us to Compose.
    reachable "${host}" "${port}" || compose_fallback
    continue
  fi

  # Docker publishes a port the moment a container starts, about half a second
  # before PostgreSQL will accept a query, so wait on the healthcheck instead.
  [[ ${container} == *"(healthy)"* ]] || compose_fallback
done <<<"${endpoints}"
