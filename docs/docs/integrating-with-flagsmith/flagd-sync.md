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

### 1. Enable the integration for the project

The flagd endpoints are **opt-in per Flagsmith project**. Until enabled, the sync and diagnostics URLs return `404`. Toggle it on with a single PATCH from a project admin:

```bash
curl -X PATCH https://api.flagsmith.com/api/v1/projects/<project_id>/integrations/flagd/<config_id>/ \
  -H 'Authorization: Token <admin-api-key>' \
  -H 'Content-Type: application/json' \
  -d '{"enabled": true}'
```

A GET on `…/integrations/flagd/` lists the current configuration (creating a disabled default row on first access if needed).

### 2. Mint a server-side environment key

The endpoint requires a server-side key (prefix `ser.`). In Flagsmith, go to **Environment Settings → SDK Keys** and create one.

### 3. Point flagd at the endpoint

The endpoint URL is:

```
GET /api/v1/flagd/flags.json
```

The endpoint accepts the key either as an `X-Environment-Key` header (for `curl` / direct HTTP clients) or as a bearer token in the `Authorization` header (for flagd, which exposes only `Authorization` via its `authHeader` config field).

Configure flagd to poll over HTTP using its `--sources` JSON:

```bash
flagd start \
  --sources='[{
    "uri": "https://api.flagsmith.com/api/v1/flagd/flags.json",
    "provider": "http",
    "authHeader": "Bearer ser.your-server-key",
    "interval": 30
  }]'
```

### 4. Evaluate flags via OpenFeature

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
    image: ghcr.io/open-feature/flagd:v0.13.2
    ports:
      - "8013:8013"   # gRPC
      - "8016:8016"   # OFREP
    command:
      - start
      - --sources=[{"uri":"https://api.flagsmith.com/api/v1/flagd/flags.json","provider":"http","authHeader":"Bearer ${FLAGSMITH_SERVER_KEY}","interval":30}]
```

### Kubernetes (flagd Helm chart values)

```yaml
flagd:
  sources:
    - uri: https://api.flagsmith.com/api/v1/flagd/flags.json
      provider: http
      interval: 30
      authHeader: "Bearer ser.your-server-key"
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
      "variants": { "control": true },
      "defaultVariant": "control"
    },
    "experiment": {
      "state": "ENABLED",
      "variants": {
        "control": "default",
        "variant_1": "treatment_a",
        "variant_2": "treatment_b"
      },
      "defaultVariant": "control",
      "targeting": {
        "fractional": [
          { "cat": [{ "var": "targetingKey" }, "experiment"] },
          ["variant_1", 30],
          ["variant_2", 30],
          ["control", 40]
        ]
      }
    },
    "premium_feature": {
      "state": "ENABLED",
      "variants": {
        "control": "free-tier",
        "override_Premium-Customers": "premium-tier"
      },
      "defaultVariant": "control",
      "targeting": {
        "if": [
          { "$ref": "Premium-Customers" },
          "override_Premium-Customers",
          "control"
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

### Variant naming

- **`control`** — the flag's typed value, served when no targeting branch matches. Always present; always the `defaultVariant`.
- **`variant_1`, `variant_2`, …** — multivariate options in declaration order.
- **`override_<segment-or-identity-slug>`** — synthesised when a segment or identity override carries a value distinct from `control`. The override's typed value lives in the variant; targeting routes to it. (flagd targeting can only return a variant *key*, never a literal value — so override values must be expressed as variants.)

There is no `off` variant. flagd's `state: DISABLED` carries the disabled signal; what a consumer receives in that case is determined by `defaultVariant` (always `"control"`) and the consumer's caller-supplied default. Override `enabled` flags are decorative for flagd consumers — operators encode "off for this segment" by setting the override's value explicitly (e.g. `false` for boolean flags).

### Segment placement

Segments referenced by **two or more** features are extracted to the top-level `$evaluators` block and referenced via `$ref` from each flag. Segments referenced by **exactly one** feature are inlined directly into that flag's `targeting`. This keeps `$evaluators` for genuinely shared definitions and avoids name collisions between feature-scoped segments that happen to share a display name.

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
| Typed value (`value`)                  | `control` variant                                         | `defaultVariant` is always `"control"`.|
| Multivariate options                   | `fractional` over generated `variant_N` variants          | Residual % maps to `"control"`.        |
| Segment override with distinct value   | `override_<slug>` variant carrying the override's value   | Routed via inline JsonLogic or `$ref`. |
| Project segment used by ≥2 features    | `$evaluators` entry, slugified key, `$ref` from each flag |                                        |
| Segment used by 1 feature              | Inlined JsonLogic in that flag's `targeting`              | No `$evaluators` entry; no name leakage.|
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

| Header               | Direction | Notes                                                                                  |
|----------------------|-----------|----------------------------------------------------------------------------------------|
| `X-Environment-Key`  | request   | Server-side key (prefix `ser.`). Required *unless* `Authorization` is provided.        |
| `Authorization`      | request   | Alternative to `X-Environment-Key`. Accepts a bare token or `Bearer <token>` form; this is what flagd's HTTP sync `authHeader` field sets. |
| `If-Modified-Since`  | request   | Optional. Returns `304` when the environment hasn't changed.                           |
| `If-None-Match`      | request   | Optional. Same effect; matched against the response `ETag`.                            |
| `Last-Modified`      | response  | Max of `environment.updated_at` and the most recent live `FeatureState.live_from` / `EnvironmentFeatureVersion.live_from`, so scheduled-change activations invalidate flagd's conditional cache. |
| `ETag`               | response  | Strong tag covering content + translator version + the same `Last-Modified` signal.    |

Status codes:

- `200` — body is the flagd document.
- `304` — short-circuit; body empty.
- `401` / `403` — missing or non-`ser.` key.
- `404` — the flagd integration isn't enabled for the project owning this environment.

For self-hosted setups behind a proxy, ensure both `Last-Modified` and `ETag` headers are forwarded so flagd can short-circuit polls efficiently.

## Diagnostics endpoint

`GET /api/v1/flagd/diagnostics.json` — same authentication as the sync endpoint, same per-project gate. Returns a structured report of translation warnings instead of a flagd document:

```json
{
  "flagSetId": "my-project/production",
  "translatorVersion": "v1",
  "environmentWarnings": [],
  "features": [
    {
      "name": "my_flag",
      "warnings": [
        {
          "reason": "regex_unsupported",
          "detail": "operator=REGEX, property=email"
        },
        {
          "reason": "type_mismatch",
          "detail": "feature=my_flag, types=[number, string]"
        }
      ]
    }
  ],
  "summary": { "featuresWithWarnings": 1, "totalWarnings": 2 }
}
```

Curl this to audit an environment before consumers depend on it. Useful in CI: fail the pipeline when `summary.totalWarnings > 0` on an environment promoted to production.

### Warning reasons

| Reason                            | What it means                                                                 |
|-----------------------------------|-------------------------------------------------------------------------------|
| `regex_unsupported`               | A segment condition uses `REGEX`; flagd has no equivalent. Condition skipped. |
| `unknown_operator`                | Internal — flagd translator hit an operator it doesn't know.                  |
| `malformed_value`                 | Value for an operator couldn't be parsed (e.g. `MODULO` value not `D|R`).     |
| `identity_override_limit_exceeded`| More identity overrides on a flag than the per-flag cap; extras dropped.     |
| `disabled_override_no_op`         | An override is `enabled=False` with value matching control — invisible to flagd. Set the override value explicitly to make it visible. |
| `type_mismatch`                   | A flag's control / multivariate / override values land in different flagd typed-flag schemas. Will fail schema validation. |

## Admin REST endpoint

`/api/v1/projects/<project_id>/integrations/flagd/` — uses Flagsmith's standard project-admin permissions, follows the same convention as every other integration toggle (Datadog, Grafana, etc.).

| Method | Effect                                                        |
|--------|---------------------------------------------------------------|
| `GET`  | List the project's flagd configuration (one row per project). |
| `POST` | Create the configuration row (body: `{"enabled": true}`).     |
| `PATCH`| Flip `enabled` on the existing row.                           |
