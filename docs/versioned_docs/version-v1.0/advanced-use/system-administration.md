---
title: System Administration
---

## Audit Logs

Every action taken within the Flagsmith administration application is tracked and logged. This allows you to easily
retrace the events and values that flags, identities and segments have taken over time.

You can view the Audit Log within the Flagsmith application, and filter it in order to find the information you are
after.

You can also stream your Audit Logs into your own infrastructure using [Audit Log Webhooks](#audit-log-webhooks).

## Audit Log Webhooks

You can use Audit Log Webhooks to stream your Organisation's Audit Log into your own infrastructure. This can be useful
for compliance or to reference against local CI/CD infrastructure.

```json
{
 "created_date": "2020-02-23T17:30:57.006318Z",
 "log": "New Flag / Remote Config created: my_feature",
 "author": {
  "id": 3,
  "email": "user@domain.com",
  "first_name": "Kyle",
  "last_name": "Johnson"
 },
 "environment": null,
 "project": {
  "id": 6,
  "name": "Project name",
  "organisation": 1
 },
 "related_object_id": 6,
 "related_object_type": "FEATURE"
}
```

## Web Hooks

You can use the Web Hooks to send events from Flagsmith into your own infrastructure. Web Hooks are managed at an
Environment level, and can be configured in the Environment settings page.

![Image](/img/add-webhook.png)

Currently the following events will generate a Web Hook action:

- Creating Features (Sent as event_type `FLAG_UPDATED`)
- Updating Feature value / state in an Environment (Sent as event_type `FLAG_UPDATED`)
- Overriding a Feature for an Identity (Sent as event_type `FLAG_UPDATED`)
- Overriding a Feature for a Segment (Sent as event_type `FLAG_UPDATED`)

You can define any number of Web Hook endpoints per Environment. Web Hooks can be managed from the Environment settings
page.

A typical use case for Web Hooks is if you want to cache flag state locally within your server environment.

Each event generates an HTTP POST with the following body payload to each of the Web Hooks defined within that
Environment:

```json
{
 "data": {
  "changed_by": "Ben Rometsch",
  "new_state": {
   "enabled": true,
   "environment": {
    "id": 23,
    "name": "Development"
   },
   "feature": {
    "created_date": "2021-02-10T20:03:43.348556Z",
    "default_enabled": false,
    "description": "Show markdown in a butter bar for certain users",
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
    "description": "Show markdown in a butter bar for certain users",
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

## Webhook Signature

When your webhook secret is set, Flagsmith uses it to create a hash signature with each payload. This hash signature is
passed with each request under the X-Flagsmith-Signature header that you need to validate at your end

### Validating Signature

Compute an HMAC with the SHA256 hash function. Use request body (raw utf-8 encoded string) as the message and secret
(utf8 encoded) as the Key. Here is one example in Python:

```python
import hmac

secret = "my shared secret"

expected_signature = hmac.new(
    key=secret.encode(),
    msg=request_body,
    digestmod=hashlib.sha256,
).hexdigest()

received_signature = request["headers"]["x-flagsmith-signature"]
hmac.compare_digest(expected_signature, received_signature) is True
```
