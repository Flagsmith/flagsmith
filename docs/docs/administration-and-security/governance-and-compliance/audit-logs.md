---
title: Audit Logs
sidebar_label: Audit Logs
sidebar_position: 30
---

Every action taken within the Flagsmith administration application is tracked and logged. This allows you to easily
retrace the events and values that flags, identities and segments have taken over time.

You can view the Audit Log within the Flagsmith application, and filter it in order to find the information you are
after.

## Audit Log Webhooks

You can stream your Audit Logs into your own infrastructure using Audit Log Webhooks. This is useful for:
- **Compliance**: Maintaining audit trails in your own systems for regulatory requirements
- **CI/CD integration**: Referencing audit log events in your local CI/CD infrastructure
- **Security monitoring**: Tracking all changes across your projects in real-time

### Setup

1. Configure a webhook endpoint in your infrastructure that accepts POST requests with the [JSON schema](#audit-log-webhook-payload) below.
2. Add the webhook URL in your Flagsmith organisation settings.
3. Optionally provide a Secret which will be [hashed and included in the HTTP header](#webhook-signature) to verify that the webhook has come from Flagsmith.

All audit log events will be sent to your webhook URL as they occur.

### Audit Log Webhook Payload

Flagsmith will send a `POST` request to your webhook URL with the following payload in the body:

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

---

## Audit Log Event Types

The following sections describe the types of events that are recorded in the Audit Log (both in the Flagsmith application and via webhooks):

### Environments

- New environment created within a project
- Environment meta-data updated

### Flags

- New flag created
- Flag state changed
- Flag deleted
- Multivariate flag state changed

### Segments

- New segment created
- Segment rule updated
- Segment condition added
- Segment condition updated
- Segment overrides re-ordered

### Identities

- Identity feature state overridden
