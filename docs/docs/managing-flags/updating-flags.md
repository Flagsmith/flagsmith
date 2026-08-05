---
title: Updating Flags (Experimental)
sidebar_label: Updating Flags (Experimental)
sidebar_position: 6
---

The `/api/experiments/environments/{environment_key}/update-flag/` endpoint lets you update feature flags, segment
overrides, and variant allocations via the Admin API.

A successful response is always **204 No Content**. The request body is a JSON object with the following fields:

- `feature` (required) — the feature to update, identified by `name` or `id`.
- `environment_default` (optional) — the default state of the feature in the environment.
- `segment_overrides` (optional) — a list of segment overrides for the feature.

Any attribute omitted in the payload will be left unchanged.

Values are passed as a `value` object with `type` and `value` (always a string):

| Type      | Example                                |
| --------- | -------------------------------------- |
| `string`  | `{"type": "string", "value": "hello"}` |
| `integer` | `{"type": "integer", "value": "42"}`   |
| `boolean` | `{"type": "boolean", "value": "true"}` |

Learn more in the
[API specification](https://api.flagsmith.com/api/v1/docs/#/experimental/api_experiments_environments_update_flag).

:::caution

**This endpoint is experimental and may change without notice.** It cannot be used when
[change requests](/administration-and-security/governance-and-compliance/change-requests) are enabled.

:::

## Examples

### Toggle a flag on or off

The simplest case — flip a feature flag in an environment.

```bash
curl -X POST 'https://api.flagsmith.com/api/experiments/environments/{environment_key}/update-flag/' \
  -H 'Authorization: Api-Key <your_token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "feature": {"name": "maintenance_mode"},
    "environment_default": {"enabled": true}
  }'
```

### Update a feature value

Change a feature's value — for example, setting a rate limit.

```bash
curl -X POST 'https://api.flagsmith.com/api/experiments/environments/{environment_key}/update-flag/' \
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

### Roll out a feature to a segment

Enable a feature for a specific segment (e.g. beta users) while keeping it off for everyone else.

```bash
curl -X POST 'https://api.flagsmith.com/api/experiments/environments/{environment_key}/update-flag/' \
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

### Configure multiple segment overrides

Set different values per segment — for example, pricing tiers.

```bash
curl -X POST 'https://api.flagsmith.com/api/experiments/environments/{environment_key}/update-flag/' \
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
        "priority": 10,
        "enabled": true,
        "value": {"type": "string", "value": "enterprise"}
      },
      {
        "segment_id": 202,
        "priority": 20,
        "enabled": true,
        "value": {"type": "string", "value": "premium"}
      }
    ]
  }'
```

When adding a new segment override, and `priority` is omitted, priority is set to the position of the override in the
`segment_overrides` list. The lowest number has the highest priority.

### Re-weight experiment variants (A/B/n)

On previously-configured experiments (multivariate features), the weight of each variant can be adjusted in the
environment and per segment with the `variants` property.

A `weight` is a percentage between 0 and 100. Any weight not allocated to variants serves the flag's default `value`.

In both `environment_default` and `segment_overrides`, the `variants` list **must** include all variants for the
feature, even if their weight is zero.

```bash
curl -X POST 'https://api.flagsmith.com/api/experiments/environments/{environment_key}/update-flag/' \
  -H 'Authorization: Api-Key <your_token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "feature": {"name": "new_payment_gateway_experiment"},
    "environment_default": {
      "enabled": true,
      "value": {"type": "string", "value": "default_gateway"},
      "variants": [
        {"key": "variant_a", "weight": 10},
        {"key": "variant_b", "weight": 10.5}
      ]
    }
  }'
```

Within the same request as above, or separately, you can also set different weights for a segment:

```bash
curl -X POST 'https://api.flagsmith.com/api/experiments/environments/{environment_key}/update-flag/' \
  -H 'Authorization: Api-Key <your_token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "feature": {"name": "new_payment_gateway_experiment"},
    "segment_overrides": [
      {
        "segment_id": 101,
        "enabled": true,
        "variants": [
          {"key": "variant_a", "weight": 25},
          {"key": "variant_b", "weight": 25}
        ]
      }
    ]
  }'
```

### Remove a segment override

A special `delete` attribute can be used to remove a segment override from a feature. It cannot be combined with other
attributes besides `segment_id`.

```bash
curl -X POST 'https://api.flagsmith.com/api/experiments/environments/{environment_key}/update-flag/' \
  -H 'Authorization: Api-Key <your_token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "feature": {"name": "new_checkout"},
    "segment_overrides": [
      {
        "segment_id": 456,
        "delete": true
      }
    ]
  }'
```
