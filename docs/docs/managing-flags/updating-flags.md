---
title: 'Experimental: Updating Flags'
sidebar_label: 'Experimental: Updating Flags'
---

We're experimenting with a set of new endpoints for updating feature flags. They should provide better ergonomics for
the most common use cases, while keeping operations agnostic to
[Feature Versioning](/managing-flags/feature-versioning). We plan to dogfood them in our own dashboard and CLI, and
eventually make them canonical.

:::caution

**These endpoints are experimental and may change without notice.** Note these limitations:

- They cannot be used when [change requests](/administration-and-security/governance-and-compliance/change-requests) are
  enabled.
- They do not support identity overrides.

These may be lifted in the future.

:::

Learn more in the [API specification](link TODO).

## Updating a flag

We support both `PATCH` and `PUT` methods for updating a flag. Both accept optional `environment_default` and
`segment_overrides` properties. Attributes omitted from a `PATCH` payload are left unchanged, while `PUT` replaces
each property it receives in full — use it with caution.

Values are passed as a `value` object with a `type` and a `value` string:

| Type      | Example                                |
| --------- | -------------------------------------- |
| `string`  | `{"type": "string", "value": "hello"}` |
| `integer` | `{"type": "integer", "value": "42"}`   |
| `boolean` | `{"type": "boolean", "value": "true"}` |

### Toggle a flag on or off

The simplest case — enable a feature flag in an environment:

```bash
curl -X PATCH 'https://api.flagsmith.com/api/__future__/environments/{environment_key}/features/{feature_id}/' \
  -H 'Authorization: Api-Key {api_key}' \
  -H 'Content-Type: application/json' \
  -d '{
    "environment_default": {"enabled": true}
  }'
```

### Update a feature value

Change a feature's default value in an environment:

```bash
curl -X PATCH 'https://api.flagsmith.com/api/__future__/environments/{environment_key}/features/{feature_id}/' \
  -H 'Authorization: Api-Key {api_key}' \
  -H 'Content-Type: application/json' \
  -d '{
    "environment_default": {
      "value": {"type": "integer", "value": "1000"}
    }
  }'
```

### Roll out a feature to a segment

Enable a flag for one or more segments, while keeping it off for everyone else:

```bash
curl -X PATCH 'https://api.flagsmith.com/api/__future__/environments/{environment_key}/features/{feature_id}/' \
  -H 'Authorization: Api-Key {api_key}' \
  -H 'Content-Type: application/json' \
  -d '{
    "environment_default": {
      "enabled": false
    },
    "segment_overrides": [
      {
        "segment": {"id": 101},
        "enabled": true,
        "priority": 10
      },
      {
        "segment": {"id": 202},
        "enabled": true,
        "priority": 20
      }
    ]
  }'
```

Segments can also override the feature's value for the environment:

```bash
curl -X PATCH 'https://api.flagsmith.com/api/__future__/environments/{environment_key}/features/{feature_id}/' \
  -H 'Authorization: Api-Key {api_key}' \
  -H 'Content-Type: application/json' \
  -d '{
    "segment_overrides": [
      {
        "segment": {"id": 101},
        "value": {"type": "string", "value": "enterprise"}
      }
    ]
  }'
```

Overrides listed in a `PATCH` payload are added or updated by segment; overrides not listed are left unchanged. When
adding a new segment override, if `priority` is omitted, it defaults to the override's position in the
`segment_overrides` list. The lowest number has the highest priority.

### Remove a segment override

To remove a segment override, `PUT` the full list of overrides without it. `PUT` replaces the whole set, deleting any
override not listed:

```bash
curl -X PUT 'https://api.flagsmith.com/api/__future__/environments/{environment_key}/features/{feature_id}/' \
  -H 'Authorization: Api-Key {api_key}' \
  -H 'Content-Type: application/json' \
  -d '{
    "segment_overrides": [
      {
        "segment": {"id": 101},
        "priority": 10,
        "value": {"type": "string", "value": "enterprise"}
      }
    ]
  }'
```

### Re-weight variants (A/B/n)

On previously configured multivariate features (e.g. experiments), the weight of each variant can be adjusted in the
environment and per segment with the `variants` property.

A `weight` is a percentage between 0 and 100. Any weight not allocated to variants serves the flag's default `value`.

Re-weight the variants for a feature in the environment:

```bash
curl -X PATCH 'https://api.flagsmith.com/api/__future__/environments/{environment_key}/features/{feature_id}/' \
  -H 'Authorization: Api-Key {api_key}' \
  -H 'Content-Type: application/json' \
  -d '{
    "environment_default": {
      "variants": [
        {"key": "variant_a", "weight": 10},
        {"key": "variant_b", "weight": 10.5}
      ]
    }
  }'
```

Within the same request as above, or separately, you can also set different weights for a segment:

```bash
curl -X PATCH 'https://api.flagsmith.com/api/__future__/environments/{environment_key}/features/{feature_id}/' \
  -H 'Authorization: Api-Key {api_key}' \
  -H 'Content-Type: application/json' \
  -d '{
    "segment_overrides": [
      {
        "segment": {"id": 101},
        "variants": [
          {"key": "variant_a", "weight": 25},
          {"key": "variant_b", "weight": 25}
        ]
      }
    ]
  }'
```

In both `environment_default` and `segment_overrides`, the `variants` list **must** include all variants for the
feature, even if their weight is zero.
