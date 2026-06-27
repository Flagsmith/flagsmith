#!/bin/sh
set -e

# Container startup is handled by the `flagsmith` entrypoint (flagsmith-common),
# which provides the serve / migrate / run-task-processor / migrate-and-serve
# verbs this script used to implement in shell.
#
# This shim stays for backwards compatibility: anything invoking the script
# path directly (Helm charts, compose files, task definitions) keeps working.
# Prefer calling `flagsmith <verb>` directly; this file can be removed once all
# consumers have migrated.
exec flagsmith "$@"
