---
title: Updating Flags (Experimental)
sidebar_label: Updating Flags (Experimental)
sidebar_position: 3
---

These endpoints let you update feature flags, segment overrides, and variant allocations via the Admin API.

:::caution

**These endpoints are experimental and may change without notice.** They cannot be used when
[change requests](/administration-and-security/governance-and-compliance/change-requests) are enabled.

:::

We're evaluating two approaches for updating flags — **Option A** (one change per request) and **Option B** (everything
in one request). Each scenario below shows both. Try them and
[let us know which works better for you](https://github.com/Flagsmith/flagsmith/issues/6233).

**Common details:**

- Identify features by `name` or `id` (pick one, not both).
- All endpoints return **204 No Content** on success.
- Omitted fields are treated as "no change" (e.g. if `enabled` is omitted, the feature's enabled state is unchanged).
- Values are passed as a `value` object with `type` and `value` (always a string):

| Type      | Example                                |
| --------- | -------------------------------------- |
| `string`  | `{"type": "string", "value": "hello"}` |
| `integer` | `{"type": "integer", "value": "42"}`   |
| `boolean` | `{"type": "boolean", "value": "true"}` |

---

## Toggle a flag on or off

The simplest case — flip a feature flag in an environment.

**Option A** —
[`POST /api/experiments/environments/{environment_key}/update-flag-v1/`](https://api.flagsmith.com/api/v1/docs/#/experimental/api_experiments_environments_update_flag_v1_create)

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

**Option B** —
[`POST /api/experiments/environments/{environment_key}/update-flag-v2/`](https://api.flagsmith.com/api/v1/docs/#/experimental/api_experiments_environments_update_flag_v2_create)

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

**Option A** —
[`POST /api/experiments/environments/{environment_key}/update-flag-v1/`](https://api.flagsmith.com/api/v1/docs/#/experimental/api_experiments_environments_update_flag_v1_create)

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

**Option B** —
[`POST /api/experiments/environments/{environment_key}/update-flag-v2/`](https://api.flagsmith.com/api/v1/docs/#/experimental/api_experiments_environments_update_flag_v2_create)

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

**Option A** —
[`POST /api/experiments/environments/{environment_key}/update-flag-v1/`](https://api.flagsmith.com/api/v1/docs/#/experimental/api_experiments_environments_update_flag_v1_create)

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

**Option B** —
[`POST /api/experiments/environments/{environment_key}/update-flag-v2/`](https://api.flagsmith.com/api/v1/docs/#/experimental/api_experiments_environments_update_flag_v2_create)

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

The `priority` field on segment overrides is optional. Omit it to add at the lowest priority. The lowest number has the
highest priority.

---

## Configure multiple segment overrides

Set different values per segment — for example, pricing tiers.

**Option A** —
[`POST /api/experiments/environments/{environment_key}/update-flag-v1/`](https://api.flagsmith.com/api/v1/docs/#/experimental/api_experiments_environments_update_flag_v1_create)

```bash
# Set environment default
curl -X POST 'https://api.flagsmith.com/api/experiments/environments/{environment_key}/update-flag-v1/' \
  -H 'Authorization: Api-Key <your_token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "feature": {"name": "pricing_tier"},
    "enabled": true,
    "value": {"type": "string", "value": "standard"}
  }'

# Set override for segment "Enterprise" (higher priority)
curl -X POST 'https://api.flagsmith.com/api/experiments/environments/{environment_key}/update-flag-v1/' \
  -H 'Authorization: Api-Key <your_token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "feature": {"name": "pricing_tier"},
    "segment": {"id": 101, "priority": 1},
    "enabled": true,
    "value": {"type": "string", "value": "enterprise"}
  }'

# Set override for segment "Premium"
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

**Option B** —
[`POST /api/experiments/environments/{environment_key}/update-flag-v2/`](https://api.flagsmith.com/api/v1/docs/#/experimental/api_experiments_environments_update_flag_v2_create)

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

## Configure A/B/n experiments (multivariate flags)

Set up multivariate flags and customise weights per segment.

Multivariate options can only be added, deleted, or updated in the environment. The `multivariate_feature_state_values`
list is absolute: omitting an option means deleting it.

Segment overrides can only re-weight existing variants. They cannot update the variant value, or add or delete
multivariate options.

**Option A** —
[`POST /api/experiments/environments/{environment_key}/update-flag-v1/`](https://api.flagsmith.com/api/v1/docs/#/experimental/api_experiments_environments_update_flag_v1_create)

```bash
# First, configure multivariate flags in the environment
curl -X POST 'https://api.flagsmith.com/api/experiments/environments/{environment_key}/update-flag-v1/' \
  -H 'Authorization: Api-Key <your_token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "feature": {"name": "new_payment_gateway_experiment"},
    "enabled": true,
    "value": {"type": "string", "value": "default"},
    "multivariate_feature_state_values": [
      {
        "percentage_allocation": 20,
        "value": {"type": "string", "value": "sharp_payments"}
      },
      {
        "percentage_allocation": 10,
        "value": {"type": "string", "value": "gemstone_express"}
      }
    ]
  }'

# Multivariate option `id`s can be fetched via the admin API
curl -X GET '/api/v1/projects/{project_id}/features/{feature_id}/mv-options/' \
  -H 'Authorization: Api-Key <your_token>' \
  -H 'Content-Type: application/json'

# You can update (add, delete, re-weight) multivariate options in the environment
curl -X POST 'https://api.flagsmith.com/api/experiments/environments/{environment_key}/update-flag-v1/' \
  -H 'Authorization: Api-Key <your_token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "feature": {"name": "new_payment_gateway_experiment"},
    "multivariate_feature_state_values": [
      {
        "multivariate_feature_option": 991,
        "percentage_allocation": 20,
        "value": {"type": "string", "value": "sharp_payments"}
      },
      {
        "percentage_allocation": 5,
        "value": {"type": "string", "value": "e-z-pay"}
      }
    ]
  }'

# Segment overrides can re-weight multivariate options (but can't add, delete, or update values)
curl -X POST 'https://api.flagsmith.com/api/experiments/environments/{environment_key}/update-flag-v1/' \
  -H 'Authorization: Api-Key <your_token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "feature": {"name": "new_payment_gateway_experiment"},
    "segment": {"id": 101, "priority": 1},
    "multivariate_feature_state_values": [
      {"multivariate_feature_option": 991, "percentage_allocation": 0},
      {"multivariate_feature_option": 993, "percentage_allocation": 100}
    ]
  }'
```

**Option B** —
[`POST /api/experiments/environments/{environment_key}/update-flag-v2/`](https://api.flagsmith.com/api/v1/docs/#/experimental/api_experiments_environments_update_flag_v2_create)

```bash
# Configure the environment default and its multivariate options
curl -X POST 'https://api.flagsmith.com/api/experiments/environments/{environment_key}/update-flag-v2/' \
  -H 'Authorization: Api-Key <your_token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "feature": {"name": "new_payment_gateway_experiment"},
    "environment_default": {
      "enabled": true,
      "value": {"type": "string", "value": "default"},
      "multivariate_feature_state_values": [
        {
          "percentage_allocation": 20,
          "value": {"type": "string", "value": "sharp_payments"}
        },
        {
          "percentage_allocation": 10,
          "value": {"type": "string", "value": "gemstone_express"}
        }
      ]
    }
  }'

# Multivariate option `id`s can be fetched via the admin API
curl -X GET '/api/v1/projects/{project_id}/features/{feature_id}/mv-options/' \
  -H 'Authorization: Api-Key <your_token>' \
  -H 'Content-Type: application/json'

# Segment overrides can re-weight multivariate options (but can't add, delete, or update values)
curl -X POST 'https://api.flagsmith.com/api/experiments/environments/{environment_key}/update-flag-v2/' \
  -H 'Authorization: Api-Key <your_token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "feature": {"name": "new_payment_gateway_experiment"},
    "segment_overrides": [
      {
        "segment_id": 101,
        "multivariate_feature_state_values": [
          {"multivariate_feature_option": 991, "percentage_allocation": 50},
          {"multivariate_feature_option": 992, "percentage_allocation": 50}
        ]
      }
    ]
  }'

# Re-weight the environment default and segment overrides in a single request
curl -X POST 'https://api.flagsmith.com/api/experiments/environments/{environment_key}/update-flag-v2/' \
  -H 'Authorization: Api-Key <your_token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "feature": {"name": "new_payment_gateway_experiment"},
    "environment_default": {
      "multivariate_feature_state_values": [
        {
          "multivariate_feature_option": 991,
          "percentage_allocation": 30,
          "value": {"type": "string", "value": "sharp_payments"}
        },
        {
          "multivariate_feature_option": 992,
          "percentage_allocation": 5,
          "value": {"type": "string", "value": "gemstone_express"}
        }
      ]
    },
    "segment_overrides": [
      {
        "segment_id": 101,
        "priority": 1,
        "multivariate_feature_state_values": [
          {"multivariate_feature_option": 991, "percentage_allocation": 100},
          {"multivariate_feature_option": 992, "percentage_allocation": 0}
        ]
      },
      {
        "segment_id": 202,
        "priority": 2,
        "multivariate_feature_state_values": [
          {"multivariate_feature_option": 991, "percentage_allocation": 0},
          {"multivariate_feature_option": 992, "percentage_allocation": 100}
        ]
      }
    ]
  }'
```

---

## Remove a segment override

A separate endpoint for removing a segment override from a feature:

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
