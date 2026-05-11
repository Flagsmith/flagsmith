---
description: Run Flagsmith + flagd together locally for OpenFeature development
sidebar_label: flagd Local Development
sidebar_position: 56
---

# Local Development with Flagsmith and flagd

This guide spins up a self-contained stack for OpenFeature work: Flagsmith as the management UI, flagd as the runtime, and your service evaluating flags through an OpenFeature provider — all on your laptop, with flag state persisted in a Postgres volume so you keep your work between restarts.

The whole thing is `docker compose up` and done — no UI clicks to mint keys, no env vars to fill in. A small bootstrap container provisions a default `local-dev` organisation / project / environment on first boot, writes the resulting server-side key to a shared volume, and flagd reads it from there. You don't think about org/project/env locally; you just author flags in the UI and they show up in flagd within seconds.

```
┌─────────────────┐    HTTP poll    ┌──────────────────┐  OpenFeature
│  Flagsmith API  │ ◄────────────── │      flagd       │ ◄──────────────┐
│  + UI :8000     │                 │  :8013 (gRPC)    │                │
│  ─────────────  │                 │  :8016 (OFREP)   │      ┌─────────┴─────────┐
│  Postgres vol.  │                 └──────────────────┘      │   your service    │
└─────────────────┘                                           └───────────────────┘
```

The walkthrough below assumes Docker, Docker Compose, and `curl`. About 5 minutes to first flag.

## 1. The compose file

A ready-to-use compose file lives at the repo root as `docker-compose.flagd-dev.yml`. Its shape:

```yaml
x-flagsmith-env: &flagsmith-env
  DATABASE_URL: postgresql://postgres:password@postgres:5432/flagsmith
  USE_POSTGRES_FOR_ANALYTICS: "true"
  DJANGO_ALLOWED_HOSTS: "*"
  DJANGO_SECRET_KEY: dev-only-secret-not-for-prod
  ENVIRONMENT: local
  PREVENT_SIGNUP: "true"
  TASK_RUN_METHOD: SYNCHRONOUSLY

volumes:
  flagsmith-pgdata:
  flagd-config:

services:
  postgres:
    image: postgres:15.5-alpine
    environment:
      POSTGRES_PASSWORD: password
      POSTGRES_DB: flagsmith
    volumes:
      - flagsmith-pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -d flagsmith -U postgres"]
      interval: 2s
      retries: 20

  flagsmith:
    image: flagsmith-flagd-dev:local        # built locally — see "First boot"
    ports: ["8000:8000"]
    environment:
      <<: *flagsmith-env
    depends_on:
      postgres:
        condition: service_healthy
    # Healthcheck is baked into the image; don't override it.

  # One-shot init: ensures a default org/project/env exists and writes
  # the resulting server-side key to a file flagd can source.
  flagsmith-bootstrap:
    image: flagsmith-flagd-dev:local
    depends_on:
      flagsmith:
        condition: service_healthy
    environment:
      <<: *flagsmith-env
    volumes:
      - flagd-config:/shared
    entrypoint: ["python", "manage.py"]
    command:
      - bootstrap_flagd_local
      - --output=/shared/flagd.env

  flagd:
    build:
      context: ./docker/flagd-launcher    # alpine + flagd binary — needs a shell
    image: flagsmith-flagd-launcher:local
    depends_on:
      flagsmith-bootstrap:
        condition: service_completed_successfully
    ports:
      - "8013:8013"   # gRPC (default flagd provider transport)
      - "8016:8016"   # OFREP (HTTP-based OpenFeature Remote Evaluation Protocol)
    volumes:
      - flagd-config:/shared:ro
    command:
      - |
        . /shared/flagd.env && \
        exec flagd start \
          --uri=http://flagsmith:8000/api/v1/flagd/flags.json \
          --sync-provider=http \
          --sync-provider-args=headers=X-Environment-Key:$$FLAGSMITH_SERVER_KEY,pollInterval=5
```

## First boot — build the Flagsmith image

Until this PR lands in a published image, build it once from your branch:

```bash
docker build -t flagsmith-flagd-dev:local --target oss-unified .
```

The `oss-unified` target bundles the API + frontend into a single image. Builds take ~5 minutes the first time and are cached after that.

Key things to note about the compose file:

- **Postgres-backed**: Flagsmith requires Postgres (some migrations use `NOW()`). The `flagsmith-pgdata` volume keeps your flags around across `docker compose down && up`.
- **`flagsmith-bootstrap` init container**: runs the `bootstrap_flagd_local` Django management command. It is idempotent — first run creates `local-dev` / `local-dev` / `development` and an `EnvironmentAPIKey`; subsequent runs reuse them. Output is written to a shared volume as `FLAGSMITH_SERVER_KEY=ser.…`.
- **flagd entrypoint sources the file**: no `.env` ferrying, no manual UI clicks, no per-user state.
- **Short poll interval (5 s)**: nice for development; set to 30–60 s in real deployments.

## 2. Bring it all up

```bash
docker compose -f docker-compose.flagd-dev.yml up -d
```

That's it. Within a few seconds:

1. Flagsmith starts (creates the Postgres DB on first boot).
2. `flagsmith-bootstrap` ensures a default org/project/env and emits the server key to `/shared/flagd.env`.
3. flagd reads the key, starts polling Flagsmith.

Confirm flagd picked up the document:

```bash
docker compose -f docker-compose.flagd-dev.yml logs flagd | grep -i sync
```

You should see flagd reporting it loaded a flag set.

## 3. Log into the Flagsmith UI

The bootstrap container creates a local admin alongside the org/project/env, with the credentials it prints to stdout (default: `admin@example.com` / `admin`). Log in at <http://localhost:8000> with those, or override via `--admin-email` / `--admin-password` on the bootstrap command if you want different ones.

You'll land in the `local-dev` organisation, with the `local-dev` project and `development` environment already there — start authoring flags.

## 4. Create a flag

Back in the Flagsmith UI, in your `Development` environment:

- Click **Create Feature**.
- Name it `welcome_banner`, set the value to `true`, leave it enabled.
- Save.

Within 5 seconds flagd will reload the document. Verify via the OFREP endpoint:

```bash
curl -s -X POST http://localhost:8016/ofrep/v1/evaluate/flags/welcome_banner \
  -H 'Content-Type: application/json' \
  -d '{"context": {"targetingKey": "user-123"}}' | jq
```

```json
{
  "key": "welcome_banner",
  "reason": "STATIC",
  "value": true,
  "variant": "on"
}
```

## 5. Evaluate from your service

Pick the OpenFeature flagd provider for your stack. Examples assume the compose stack above (gRPC on `localhost:8013`).

### Python

```python
from openfeature import api
from openfeature.contrib.provider.flagd import FlagdProvider

api.set_provider(FlagdProvider(host="localhost", port=8013))
client = api.get_client()

ctx = {"targetingKey": "user-123", "tier": "premium"}
print(client.get_boolean_value("welcome_banner", default_value=False, evaluation_context=ctx))
```

### Node / TypeScript

```ts
import { OpenFeature } from '@openfeature/server-sdk';
import { FlagdProvider } from '@openfeature/flagd-provider';

await OpenFeature.setProviderAndWait(new FlagdProvider({ host: 'localhost', port: 8013 }));
const client = OpenFeature.getClient();

const enabled = await client.getBooleanValue('welcome_banner', false, {
  targetingKey: 'user-123',
});
console.log(enabled);
```

### Go

```go
import (
    "github.com/open-feature/go-sdk/openfeature"
    flagd "github.com/open-feature/go-sdk-contrib/providers/flagd/pkg"
)

openfeature.SetProvider(flagd.NewProvider(flagd.WithHost("localhost"), flagd.WithPort(8013)))
client := openfeature.NewClient("local-dev")

enabled, _ := client.BooleanValue(ctx, "welcome_banner", false,
    openfeature.NewEvaluationContext("user-123", nil))
```

## 6. Wiring your service into the compose stack

To run your service alongside Flagsmith and flagd, add another service entry:

```yaml
  my-service:
    build: .
    depends_on:
      - flagd
    environment:
      FLAGD_HOST: flagd
      FLAGD_PORT: "8013"
```

Inside the compose network, flagd is reachable as `flagd:8013` (gRPC) or `flagd:8016` (OFREP).

## What does the env key actually scope?

The server-side key (`ser.…`) you mint above pins the request to **one specific Environment** in Flagsmith. From there, the project and organisation are implied through foreign keys:

- The lookup is `Environment.get_from_cache(api_key)`; the env carries `project` (which carries `organisation`).
- `organisation.stop_serving_flags` will reject the request if the org is paused.
- The `ser.` prefix is what allows the request through `EnvironmentKeyAuthentication(required_key_prefix="ser.")` — client-side keys (no prefix) are rejected.

So one env key = one environment = one flagd flag-set. To target multiple Flagsmith environments from a single flagd, run multiple flagd sync sources — one per env key.

## Resetting your local stack

```bash
docker compose -f docker-compose.flagd-dev.yml down       # keep data
docker compose -f docker-compose.flagd-dev.yml down -v    # wipe Postgres volume
```

The named `flagsmith-pgdata` volume is the only persistent state. Delete it if you want a fresh org/project tree.

## Troubleshooting

- **flagd logs `unauthorized`** — the `FLAGSMITH_SERVER_KEY` doesn't start with `ser.` or doesn't match an environment. Mint a new server-side key in the UI.
- **flagd logs `404`** — the URL is wrong; the compose example uses `flagsmith:8000` as the in-network hostname.
- **Flag changes don't show up** — check `pollInterval`; the example uses 5 s. Also confirm the response: `curl -s -H "X-Environment-Key: ser.…" http://localhost:8000/api/v1/flagd/flags.json | jq '.metadata'` should show a fresh `version` after each change.
- **`metadata.flagsmith.warnings` present** — the environment has rules that don't translate cleanly (typically REGEX). Consult the [compatibility matrix](./flagd-sync.md#compatibility-matrix).
