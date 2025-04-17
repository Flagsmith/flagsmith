# Local maintenance utilities

This directory contains scripts to help running and maintaining the Flagsmith
API in the local environment.

## Requirements

- Docker

That's it. These scripts are designed to interact with the application runtime
through ephemeral Docker containers.

## Scripts

### `bin/run`

Runs any command within the `api` container. Examples:

- `bin/run` — runs pending migrations and starts the API HTTP server in dev mode.
- `bin/run bash` — starts a bash shell in the API container.
- `bin/run python manage.py makemigrations` — runs the command in the API container.
- `bin/run flagsmith createsuperuser` — the Flagsmith CLI should be there too!
- `bin/run pytest --sw --pdb api/tests/unit/test_my_feature.py` — you get it.

> This script is intended as a one-command option to run Flagsmith code with no
> previous setup except from installing Docker.
