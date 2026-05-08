---
description: Use Flagsmith as a flagd HTTP sync source
sidebar_label: flagd Sync Source
sidebar_position: 55
---

# flagd Sync Source

**Flagsmith is the management UI for your flagd deployment.** Authors create flags, segments, and identity overrides in Flagsmith; Flagsmith emits a [flagd](https://flagd.dev)-compatible flag-definition document on an HTTP sync endpoint; flagd polls it, loads the document, and evaluates flags in-process via OpenFeature.

The Flagsmith SDK is **not** part of this topology. In this mode the Flagsmith UI is a pure authoring surface — your services never call Flagsmith directly. They evaluate via flagd, which is the runtime source of truth.

This is the right setup when:

- You already run flagd in your platform and want a UI / audit log / segmentation tooling on top.
- You want OpenFeature-native evaluation across many services without operating a per-language SDK.

## Architecture

```
┌──────────┐  HTTP poll   ┌───────────────────┐
│  flagd   │ ───────────> │  Flagsmith API    │
│ (runtime)│              │  /api/v1/flagd/   │
└────┬─────┘              │  flags.json       │
     │                    └───────────────────┘
     │ OpenFeature provider (gRPC / OFREP / in-process)
     ▼
┌──────────────┐
│ your service │
└──────────────┘
```

## Quick start

### 1. Mint a server-side environment key

The endpoint requires a server-side key (prefix `ser.`). In Flagsmith, go to **Environment Settings → SDK Keys** and create one.

### 2. Point flagd at the endpoint

The endpoint URL is:

```
GET /api/v1/flagd/flags.json
```

Authenticate via the `X-Environment-Key` header. Configure flagd to poll over HTTP:

```bash
flagd start \
  --uri https://api.flagsmith.com/api/v1/flagd/flags.json \
  --sync-provider http \
  --sync-provider-args headers=X-Environment-Key:ser.your-server-key,pollInterval=30
```

### 3. Evaluate flags via OpenFeature

flagd exposes evaluation through gRPC, OFREP, and in-process providers. Pick the OpenFeature [flagd provider](https://flagd.dev/reference/providers/) for your language:

#### Go

```go
import (
    "github.com/open-feature/go-sdk/openfeature"
    flagd "github.com/open-feature/go-sdk-contrib/providers/flagd/pkg"
)

openfeature.SetProvider(flagd.NewProvider())
client := openfeature.NewClient("my-app")

enabled, _ := client.BooleanValue(ctx, "my_flag", false, openfeature.NewEvaluationContext("user-123", map[string]interface{}{
    "tier": "premium",
}))
```

#### Python

```python
from openfeature import api
from openfeature.contrib.provider.flagd import FlagdProvider

api.set_provider(FlagdProvider())  # defaults to localhost:8013
client = api.get_client()

ctx = {"targetingKey": "user-123", "tier": "premium"}
enabled = client.get_boolean_value("my_flag", False, ctx)
```

#### Node / TypeScript

```ts
import { OpenFeature } from '@openfeature/server-sdk';
import { FlagdProvider } from '@openfeature/flagd-provider';

await OpenFeature.setProviderAndWait(new FlagdProvider());
const client = OpenFeature.getClient();

const enabled = await client.getBooleanValue('my_flag', false, {
  targetingKey: 'user-123',
  tier: 'premium',
});
```

The `targetingKey` is what flagd hashes for `fractional` (multivariate) evaluation, so use a stable per-user identifier.

## Deployment recipes

### docker-compose

```yaml
services:
  flagd:
    image: ghcr.io/open-feature/flagd:latest
    ports:
      - "8013:8013"   # gRPC
      - "8016:8016"   # OFREP
    command:
      - start
      - --uri=https://api.flagsmith.com/api/v1/flagd/flags.json
      - --sync-provider=http
      - --sync-provider-args=headers=X-Environment-Key:${FLAGSMITH_SERVER_KEY},pollInterval=30
```

### Kubernetes (flagd Helm chart values)

```yaml
flagd:
  sources:
    - uri: https://api.flagsmith.com/api/v1/flagd/flags.json
      provider: http
      interval: 30
      headers:
        X-Environment-Key: ser.your-server-key
```

For self-hosted Flagsmith deployments, replace the host with your own.

### Polling interval

30–60 seconds is a sensible default. The endpoint sets `Last-Modified` and a strong `ETag`, so unchanged environments return `304 Not Modified` with an empty body — short intervals are cheap.

## Document anatomy

A successful response body looks like:

```json
{
  "$schema": "https://flagd.dev/schema/v0/flags.json",
  "flags": {
    "my_flag": {
      "state": "ENABLED",
      "variants": { "on": true, "off": false },
      "defaultVariant": "on"
    },
    "experiment": {
      "state": "ENABLED",
      "variants": {
        "on": "control",
        "variant_1": "treatment_a",
        "variant_2": "treatment_b",
        "off": ""
      },
      "defaultVariant": "on",
      "targeting": {
        "fractional": [
          { "cat": [{ "var": "targetingKey" }, "experiment"] },
          ["variant_1", 30],
          ["variant_2", 30],
          ["on", 40]
        ]
      }
    }
  },
  "$evaluators": {
    "Premium-Customers": { "==": [{ "var": "tier" }, "premium"] }
  },
  "metadata": {
    "flagSetId": "my-project/production",
    "version": "2026-05-08T10:42:11+00:00",
    "flagsmith.environmentId": 42,
    "flagsmith.translatorVersion": "v1"
  }
}
```

### Metadata fields

- **`flagSetId`** — `"<project-slug>/<environment-slug>"`. Stable across renames within Flagsmith only if you don't rename; consumer-side caches keyed on this should expect changes.
- **`version`** — ISO timestamp of the environment's last update; useful for detecting fresh documents in dashboards.
- **`flagsmith.environmentId`** — numeric Flagsmith environment id (helpful for support tickets).
- **`flagsmith.translatorVersion`** — bumped when this translator's output format changes; treat new versions as cache-invalidating.
- **`flagsmith.warnings`** — JSON-encoded list of translation warnings; only present when an environment contains content that couldn't be fully translated. Parse it once at startup to surface gaps.

## Compatibility matrix

| Flagsmith concept                      | flagd translation                                         | Notes                                  |
|----------------------------------------|-----------------------------------------------------------|----------------------------------------|
| Boolean flag (`enabled`)               | `state: ENABLED`/`DISABLED`                               | Always emitted.                        |
| Typed value (`value`)                  | Variant `"on"` (typed) and `"off"` (type-zero)            | `defaultVariant` follows `enabled`.    |
| Multivariate options                   | `fractional` over generated variants                      | Residual % maps to `"on"`.             |
| Segment                                | `$evaluators` entry, slugified key                        | Referenced from `targeting` via `$ref`.|
| Segment rule type ALL                  | JsonLogic `and`                                           |                                        |
| Segment rule type ANY                  | JsonLogic `or`                                            |                                        |
| Segment rule type NONE                 | JsonLogic `!` over `or`                                   |                                        |
| `EQUAL`, `NOT_EQUAL`                   | `==`, `!=`                                                | With best-effort native typing.        |
| `GREATER_THAN`(`_INCLUSIVE`), `LESS_*` | `>`, `>=`, `<`, `<=`                                      | Numeric coercion.                      |
| `CONTAINS`, `NOT_CONTAINS`             | `in` (substring), wrapped in `!` for negation             |                                        |
| `IN`                                   | JsonLogic `in` against a list                             | Values split on `,`.                   |
| `MODULO`                               | `{"==": [{"%": [var, D]}, R]}`                           | Value format `"D|R"`.                  |
| `IS_SET`, `IS_NOT_SET`                 | Null comparison                                           |                                        |
| SemVer comparisons                     | `sem_ver` flagd custom op                                 | Recognised by `:semver` value suffix.  |
| `PERCENTAGE_SPLIT` in segment rules    | `fractional` two-bucket trick                             | flagd owns bucketing.                  |
| Identity overrides                     | `targetingKey` equality, chained                          | Capped at 100 per flag (configurable). |
| **`REGEX` operator**                   | **Skipped** — not supported by flagd                      | Warning surfaced in `metadata`.        |

## Unsupported features

- **REGEX segment operator** — skipped; flagd has no equivalent custom op.
- **Change-request previews** — only the active environment state is exposed.
- **Identities created on the flagd side** — Flagsmith never sees them; create identities in Flagsmith if you need persistent overrides.

## Endpoint reference

`GET /api/v1/flagd/flags.json`

| Header               | Direction | Notes                                                         |
|----------------------|-----------|---------------------------------------------------------------|
| `X-Environment-Key`  | request   | Required. Must be a server-side key (prefix `ser.`).          |
| `If-Modified-Since`  | request   | Optional. Returns `304` when the environment hasn't changed.  |
| `If-None-Match`      | request   | Optional. Same effect; matched against the response `ETag`.   |
| `Last-Modified`      | response  | The environment's `updated_at`.                               |
| `ETag`               | response  | Strong tag covering content + translator version.             |

Status codes:

- `200` — body is the flagd document.
- `304` — short-circuit; body empty.
- `401` / `403` — missing or non-`ser.` key.

For self-hosted setups behind a proxy, ensure both `Last-Modified` and `ETag` headers are forwarded so flagd can short-circuit polls efficiently.
