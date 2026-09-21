#!/usr/bin/env bash
# A faster alternative to `docker compose up --wait` (around ~0.15s vs ~2s on average).
set -euo pipefail

project="${COMPOSE_PROJECT_NAME:-flagsmith}"

# Pull "host port" out of a URL like postgresql://user:pw@host:5432/name.
endpoint_of() {
  sed -E 's#^[^:]+://([^@]*@)?([^:/]+):([0-9]+).*$#\2 \3#' <<<"$1"
}

endpoints=$(
  {
    endpoint_of "${TEST_DATABASE_URL:-${DATABASE_URL:-}}"
    endpoint_of "${TEST_ANALYTICS_DATABASE_URL:-${ANALYTICS_DATABASE_URL:-}}"
    printf '%s %s\n' "${CLICKHOUSE_HOST:-localhost}" "${CLICKHOUSE_PORT:-9000}"
  } | sort -u
)

reachable() {
  (exec 3<>"/dev/tcp/$1/$2") 2>/dev/null
}

compose_fallback() {
  exec docker compose up --remove-orphans --wait -d
}

containers=$(
  # an equivalent compose command is x25 slower
  docker ps --filter "label=com.docker.compose.project=${project}" \
    --format '{{.Ports}} {{.Status}}'
) || compose_fallback

while read -r host port; do
  container=$(grep ":${port}->" <<<"${containers}" || true)

  if [[ -z ${container} ]]; then
    reachable "${host}" "${port}" || compose_fallback
    continue
  fi

  [[ ${container} == *"(healthy)"* ]] || compose_fallback
done <<<"${endpoints}"
