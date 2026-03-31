---
title: Updating Flags
sidebar_label: Updating Flags
sidebar_position: 3
---

These experimental endpoints let you update feature flag values and segment overrides via the Admin API. They're
purpose-built for automation and CI/CD — minimal payloads, no need to look up internal IDs, and they work the same
regardless of whether your environment uses v1 or v2 feature versioning.

:::caution

These endpoints are experimental and may change without notice. They do not support multivariate values and cannot be
used when [change requests](/administration-and-security/governance-and-compliance/change-requests) are enabled.

:::

We're evaluating two approaches for updating flags — **Option A** (one change per request) and **Option B** (everything
in one request). Each scenario below shows both. Try them and
[let us know which works better for you](https://github.com/Flagsmith/flagsmith/issues/6233).

**Common details:**

- Identify features by `name` or `id` (pick one, not both).
- All endpoints return **204 No Content** on success.
- Values are passed as a `value` object with `type` and `value` (always a string):

| Type      | Example                                          |
| --------- | ------------------------------------------------ |
| `string`  | `{"type": "string", "value": "hello"}`           |
| `integer` | `{"type": "integer", "value": "42"}`             |
| `boolean` | `{"type": "boolean", "value": "true"}`           |

---

## Toggle a flag on or off

The simplest case — flip a feature flag in an environment.

**Option A** — [`POST /api/experiments/environments/{environment_key}/update-flag-v1/`](https://api.flagsmith.com/api/v1/docs/#/experimental/api_experiments_environments_update_flag_v1_create)

```bash
curl -X POST 'https://api.flagsmith.com/api/experiments/environments/{environment_key}/update-flag-v1/' \
  -H 'Authorization: Api-Key <your_token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "feature": {"name": "maintenance_mode"},
    "enabled": true,
    "value": {"type": "boolean", "value": "true"}
  }'
```

**Option B** — [`POST /api/experiments/environments/{environment_key}/update-flag-v2/`](https://api.flagsmith.com/api/v1/docs/#/experimental/api_experiments_environments_update_flag_v2_create)

```bash
curl -X POST 'https://api.flagsmith.com/api/experiments/environments/{environment_key}/update-flag-v2/' \
  -H 'Authorization: Api-Key <your_token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "feature": {"name": "maintenance_mode"},
    "environment_default": {
      "enabled": true,
      "value": {"type": "boolean", "value": "true"}
    }
  }'
```

---

## Update a feature value

Change a feature's value — for example, setting a rate limit.

**Option A**

```bash
curl -X POST 'https://api.flagsmith.com/api/experiments/environments/{environment_key}/update-flag-v1/' \
  -H 'Authorization: Api-Key <your_token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "feature": {"name": "api_rate_limit"},
    "enabled": true,
    "value": {"type": "integer", "value": "1000"}
  }'
```

**Option B**

```bash
curl -X POST 'https://api.flagsmith.com/api/experiments/environments/{environment_key}/update-flag-v2/' \
  -H 'Authorization: Api-Key <your_token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "feature": {"name": "api_rate_limit"},
    "environment_default": {
      "enabled": true,
      "value": {"type": "integer", "value": "1000"}
    }
  }'
```

---

## Roll out a feature to a segment

Enable a feature for a specific segment (e.g. beta users) while keeping it off for everyone else.

**Option A**

```bash
curl -X POST 'https://api.flagsmith.com/api/experiments/environments/{environment_key}/update-flag-v1/' \
  -H 'Authorization: Api-Key <your_token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "feature": {"name": "new_checkout"},
    "segment": {"id": 456},
    "enabled": true,
    "value": {"type": "boolean", "value": "true"}
  }'
```

**Option B** — single request:

```bash
curl -X POST 'https://api.flagsmith.com/api/experiments/environments/{environment_key}/update-flag-v2/' \
  -H 'Authorization: Api-Key <your_token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "feature": {"name": "new_checkout"},
    "environment_default": {
      "enabled": false,
      "value": {"type": "boolean", "value": "false"}
    },
    "segment_overrides": [
      {
        "segment_id": 456,
        "enabled": true,
        "value": {"type": "boolean", "value": "true"}
      }
    ]
  }'
```

The `priority` field on segment overrides is optional. Omit it to add at the lowest priority. Priority `1` is highest.

---

## Configure multiple segment overrides

Set different values per segment — for example, pricing tiers.

**Option A** — one request per segment override plus one for the default:

```bash
# Default
curl -X POST 'https://api.flagsmith.com/api/experiments/environments/{environment_key}/update-flag-v1/' \
  -H 'Authorization: Api-Key <your_token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "feature": {"name": "pricing_tier"},
    "enabled": true,
    "value": {"type": "string", "value": "standard"}
  }'

# Enterprise segment (highest priority)
curl -X POST 'https://api.flagsmith.com/api/experiments/environments/{environment_key}/update-flag-v1/' \
  -H 'Authorization: Api-Key <your_token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "feature": {"name": "pricing_tier"},
    "segment": {"id": 101, "priority": 1},
    "enabled": true,
    "value": {"type": "string", "value": "enterprise"}
  }'

# Premium segment
curl -X POST 'https://api.flagsmith.com/api/experiments/environments/{environment_key}/update-flag-v1/' \
  -H 'Authorization: Api-Key <your_token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "feature": {"name": "pricing_tier"},
    "segment": {"id": 202, "priority": 2},
    "enabled": true,
    "value": {"type": "string", "value": "premium"}
  }'
```

**Option B** — single request:

```bash
curl -X POST 'https://api.flagsmith.com/api/experiments/environments/{environment_key}/update-flag-v2/' \
  -H 'Authorization: Api-Key <your_token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "feature": {"name": "pricing_tier"},
    "environment_default": {
      "enabled": true,
      "value": {"type": "string", "value": "standard"}
    },
    "segment_overrides": [
      {
        "segment_id": 101,
        "priority": 1,
        "enabled": true,
        "value": {"type": "string", "value": "enterprise"}
      },
      {
        "segment_id": 202,
        "priority": 2,
        "enabled": true,
        "value": {"type": "string", "value": "premium"}
      }
    ]
  }'
```

---

## Remove a segment override

Removes a segment override from a feature.

[`POST /api/experiments/environments/{environment_key}/delete-segment-override/`](https://api.flagsmith.com/api/v1/docs/#/experimental/api_experiments_environments_delete_segment_override_create)

```bash
curl -X POST 'https://api.flagsmith.com/api/experiments/environments/{environment_key}/delete-segment-override/' \
  -H 'Authorization: Api-Key <your_token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "feature": {"name": "pricing_tier"},
    "segment": {"id": 202}
  }'
```

---

## Quick reference

| Aspect               | Details                                                                      |
| -------------------- | ---------------------------------------------------------------------------- |
| Feature ID           | `name` or `id` — use one, not both                                           |
| Value types          | `string`, `integer`, `boolean`                                               |
| Segment priority     | Optional — omit to add at lowest priority; `1` is highest                    |
| Feature versioning   | Works the same on v1 and v2 environments                                     |
| Success response     | `204 No Content`                                                             |
| Limitations          | No multivariate support; incompatible with change requests                   |
| Full API schema      | [Swagger Explorer](https://api.flagsmith.com/api/v1/docs/)                   |
