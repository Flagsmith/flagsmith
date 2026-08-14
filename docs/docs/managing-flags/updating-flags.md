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

Learn more in the [API specification](https://api.flagsmith.com/api/v1/docs/#/experimental).

## Updating a flag

We support both `PATCH` and `PUT` methods for updating a flag. Both accept optional `environment_default` and
`segment_overrides` properties. Attributes omitted from a `PATCH` payload are left unchanged, while `PUT` replaces each
property it receives in full — use it with caution.

Values are passed as a `value` object with a `type` and a `value` string:

| Type      | Example                                |
| --------- | -------------------------------------- |
| `string`  | `{"type": "string", "value": "hello"}` |
| `integer` | `{"type": "integer", "value": "42"}`   |
| `boolean` | `{"type": "boolean", "value": "true"}` |

Both methods respond with the flag's complete state in the environment, whichever properties were sent.

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

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "environment_default": {"enabled": true, "value": {"type": "string", "value": "hello"}, "variants": []},
  "segment_overrides": []
}
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

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "environment_default": {"enabled": true, "value": {"type": "integer", "value": "1000"}, "variants": []},
  "segment_overrides": []
}
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

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "environment_default": {"enabled": false, "value": {"type": "string", "value": "standard"}, "variants": []},
  "segment_overrides": [
    {
      "segment": {"id": 101},
      "priority": 10,
      "enabled": true,
      "value": {"type": "string", "value": "standard"},
      "variants": []
    },
    {
      "segment": {"id": 202},
      "priority": 20,
      "enabled": true,
      "value": {"type": "string", "value": "standard"},
      "variants": []
    }
  ]
}
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

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "environment_default": {"enabled": false, "value": {"type": "string", "value": "standard"}, "variants": []},
  "segment_overrides": [
    {
      "segment": {"id": 101},
      "priority": 10,
      "enabled": true,
      "value": {"type": "string", "value": "enterprise"},
      "variants": []
    },
    {
      "segment": {"id": 202},
      "priority": 20,
      "enabled": true,
      "value": {"type": "string", "value": "standard"},
      "variants": []
    }
  ]
}
```

Overrides listed in a `PATCH` payload are added or updated by segment; overrides not listed are left unchanged. When
adding a new segment override, if `priority` is omitted, it defaults to the override's position in the
`segment_overrides` list. The lowest number has the highest priority.

A new segment override serves whatever the environment default serves, until you give it a `value` of its own. An
existing override keeps its priority unless you send a new one.

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

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "environment_default": {"enabled": false, "value": {"type": "string", "value": "standard"}, "variants": []},
  "segment_overrides": [
    {
      "segment": {"id": 101},
      "priority": 10,
      "enabled": false,
      "value": {"type": "string", "value": "enterprise"},
      "variants": []
    }
  ]
}
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
        {"id": 33, "weight": 10},
        {"id": 34, "weight": 10.5}
      ]
    }
  }'
```

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "environment_default": {
    "enabled": true,
    "value": {"type": "string", "value": "control"},
    "variants": [
      {"id": 33, "weight": 10},
      {"id": 34, "weight": 10.5}
    ]
  },
  "segment_overrides": []
}
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
          {"id": 33, "weight": 25},
          {"id": 34, "weight": 25}
        ]
      }
    ]
  }'
```

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "environment_default": {
    "enabled": true,
    "value": {"type": "string", "value": "control"},
    "variants": [
      {"id": 33, "weight": 10},
      {"id": 34, "weight": 10.5}
    ]
  },
  "segment_overrides": [
    {
      "segment": {"id": 101},
      "priority": 0,
      "enabled": true,
      "value": {"type": "string", "value": "control"},
      "variants": [
        {"id": 33, "weight": 25},
        {"id": 34, "weight": 25}
      ]
    }
  ]
}
```

When present, in both `environment_default` and `segment_overrides`, the `variants` list **must** include all variants
for the feature, even if their weight is zero.

Because `PUT` replaces `environment_default` in full, it **must** carry `variants` for a multivariate feature. A segment
override that omits `variants` inherits the weights of the environment default, unless `PATCH` is updating an existing
override, which keeps its own weights.
