#!/usr/bin/env bash
# Make sure the local Compose services are reachable, cheaply.
#
# `docker compose up --wait` is the correct thing to run, but it needs a couple
# of seconds just to parse the project and talk to the daemon -- a large slice
# of a focused `make test`. Opening a socket to each service costs a
# millisecond and answers the same question in the overwhelmingly common case
# where the stack is already up, so try that first and fall back to Compose.
set -euo pipefail

# Pull "host" and "port" out of a URL like postgresql://user:pw@host:5432/name.
endpoint_of() {
  sed -E 's#^[^:]+://([^@]*@)?([^:/]+):([0-9]+).*$#\2 \3#' <<<"$1"
}

reachable() {
  # Bash's /dev/tcp needs no subprocess, unlike nc(1), which is not everywhere.
  (exec 3<>"/dev/tcp/$1/$2") 2>/dev/null
}

services=(
  "$(endpoint_of "${TEST_DATABASE_URL:-${DATABASE_URL}}")"
  "$(endpoint_of "${TEST_ANALYTICS_DATABASE_URL:-${ANALYTICS_DATABASE_URL}}")"
  "${CLICKHOUSE_HOST:-localhost} ${CLICKHOUSE_PORT:-9000}"
)

for service in "${services[@]}"; do
  # shellcheck disable=SC2086 # deliberate split into host and port
  reachable ${service} || exec docker compose up --remove-orphans --wait -d
done
