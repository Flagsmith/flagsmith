---
title: Environment Settings
sidebar_label: Environment Settings
sidebar_position: 10
---

## Use Consistent Hashing

This setting allows legacy environments to manually choose to update the hashing algorithm used by the engine when
evaluating multivariate and percentage splits. Enabling this setting ensures that identities that are evaluated across
the Core API, Edge API and local evaluation mode in our server side SDKs receive the same multivariate variations and
appear in the same segments that use the percentage split operator. All new environments are created with this setting
enabled by default.

:::caution

This will result in identities receiving different variations and being evaluated in different segments (that use the %
split operator) when evaluated against the remote API. Evaluations in local evaluation mode will not be affected.

:::

## Environment Webhooks

Environment webhooks allow you to send flag change events from Flagsmith into your own infrastructure. Webhooks are managed at an Environment level and can be configured in the Environment settings page.

This is particularly useful for:
- **Custom caching behaviour**: Updating your local cache when flags change in an environment
- **Real-time synchronisation**: Keeping external systems in sync with flag states
- **Event-driven architectures**: Triggering downstream processes when flags are updated

### Setup

1. Configure a webhook endpoint in your infrastructure that accepts POST requests with the [JSON schema](#environment-webhook-payload) below.
2. Add the webhook URL in your Environment settings.
3. Optionally provide a Secret which will be [hashed and included in the HTTP header](#webhook-signature) to verify that the webhook has come from Flagsmith.

You can define any number of webhook endpoints per environment. Each event will generate an HTTP POST to all configured webhook URLs.

### Events That Trigger Webhooks

The following events will generate a webhook action (all sent as `event_type: "FLAG_UPDATED"`):

- Creating features
- Updating a feature value/state in an environment
- Overriding a feature for an identity
- Overriding a feature for a segment

### Environment Webhook Payload

Flagsmith will send a `POST` request to your webhook URL with the following payload in the body:

```json
{
 "data": {
  "changed_by": "user@domain.com",
  "new_state": {
   "enabled": true,
   "environment": {
    "id": 23,
    "name": "Development"
   },
   "feature": {
    "created_date": "2021-02-10T20:03:43.348556Z",
    "default_enabled": false,
    "description": "Show html in a butter bar for certain users",
    "id": 7168,
    "initial_value": null,
    "name": "butter_bar",
    "project": {
     "id": 12,
     "name": "Flagsmith Website"
    },
    "type": "CONFIG"
   },
   "feature_segment": null,
   "feature_state_value": "<strong>\nYou are using the develop environment.\n</strong>",
   "identity": null,
   "identity_identifier": null
  },
  "previous_state": {
   "enabled": false,
   "environment": {
    "id": 23,
    "name": "Development"
   },
   "feature": {
    "created_date": "2021-02-10T20:03:43.348556Z",
    "default_enabled": false,
    "description": "Show html in a butter bar for certain users",
    "id": 7168,
    "initial_value": null,
    "name": "butter_bar",
    "project": {
     "id": 12,
     "name": "Flagsmith Website"
    },
    "type": "CONFIG"
   },
   "feature_segment": null,
   "feature_state_value": "<strong>\nYou are using the develop environment.\n</strong>",
   "identity": null,
   "identity_identifier": null
  },
  "timestamp": "2021-06-18T07:50:26.595298Z"
 },
 "event_type": "FLAG_UPDATED"
}
```

### Webhook Signature

When your webhook secret is set, Flagsmith uses it to create a hash signature with each payload. This hash signature is passed with each request under the `X-Flagsmith-Signature` header that you need to validate at your end.

#### Validating Signature

Compute an HMAC with the SHA256 hash function. Use request body (raw utf-8 encoded string) as the message and secret (utf8 encoded) as the Key. Here is one example in Python:

```python
import hmac
import hashlib

secret = "my shared secret"

expected_signature = hmac.new(
    key=secret.encode(),
    msg=request_body,
    digestmod=hashlib.sha256,
).hexdigest()

received_signature = request["headers"]["x-flagsmith-signature"]
hmac.compare_digest(expected_signature, received_signature) is True
```

## Custom fields

Optional or required custom fields can be defined when creating or updating environments.
[Learn more](/administration-and-security/governance-and-compliance/custom-fields)
