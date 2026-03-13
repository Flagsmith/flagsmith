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

## Related Object Types

The `related_object_type` field in the audit log payload indicates the type of resource that was affected. The possible
values are:

| Value               | Description                    |
| ------------------- | ------------------------------ |
| `FEATURE`           | Feature (flag / remote config) |
| `FEATURE_STATE`     | Feature state                  |
| `SEGMENT`           | Segment                        |
| `ENVIRONMENT`       | Environment                    |
| `CHANGE_REQUEST`    | Change request                 |
| `EDGE_IDENTITY`     | Edge identity                  |
| `IMPORT_REQUEST`    | Import request                 |
| `EF_VERSION`        | Environment feature version    |
| `FEATURE_HEALTH`    | Feature health status          |
| `RELEASE_PIPELINE`  | Release pipeline               |

## Audit Log Event Types

The following sections describe the types of events that are recorded in the Audit Log (both in the Flagsmith
application and via webhooks):

### Environments

- New environment created
- Environment updated

### Flags

- New flag / remote config created
- Flag / remote config updated
- Flag / remote config deleted
- Multivariate option added to or removed from a feature
- Multivariate value changed for a feature

### Segments

- New segment created
- Segment updated
- Segment deleted

### Flag State Changes

- Flag state updated for a feature
- Remote config value updated for a feature
- Flag state / remote config value update scheduled
- Scheduled change went live (via change request)
- Flag state scheduled for update by a change request
- Flag state / remote config updated by a change request

### Identity Overrides

- Identity override created
- Identity override updated (flag state / remote config value)
- Identity override value updated (remote config)
- Identity override deleted
- Identity override scheduled
- Edge identity feature override created, updated, or deleted

### Segment Overrides

- Segment override created
- Segment override updated (flag state / remote config value)
- Segment override value updated (remote config)
- Segment override deleted
- Segment override scheduled
- Segment rules updated for a flag in an environment
- Segment overrides re-ordered for a feature

### Change Requests

- Change request created
- Change request approved
- Change request committed
- Change request deleted

### Feature Versioning

- New version published for a feature

### Release Pipelines

- Release pipeline created
- Release pipeline cloned
- Release pipeline updated
- Release pipeline published
- Release pipeline converted to draft (unpublished)
- Release pipeline deleted
- Feature added to a release pipeline
- Feature removed from a release pipeline
- Flag state / remote config updated by a release pipeline

### Phased Rollouts

- Phased rollout created for a feature by a release pipeline
- Phased rollout split percentage changed
