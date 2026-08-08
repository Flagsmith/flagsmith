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
 "related_object_uuid": null,
 "related_object_type": "FEATURE"
}
```

`related_object_type` is one of: `FEATURE`, `FEATURE_STATE`, `SEGMENT`, `ENVIRONMENT`, `CHANGE_REQUEST`, `EDGE_IDENTITY`, `IMPORT_REQUEST`, `EF_VERSION`, `FEATURE_HEALTH`.

`related_object_id` is the integer primary key of the related object; `related_object_uuid` is its UUID. Which field is populated depends on the audit type. `EF_VERSION` and `EDGE_IDENTITY` entries populate only `related_object_uuid`. `SEGMENT` deletion entries populate both. Other entries populate `related_object_id`. When parsing, check both fields.

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

## Audit Log Event Types

Each record carries a `related_object_type` and a `log` string. The tables below enumerate every event Flagsmith
emits, grouped by `related_object_type`. Placeholders in angle brackets (e.g. `<name>`, `<identifier>`, `<datetime>`)
are substituted with the affected resource's values at the time of the event.

The Deployment column indicates where each event is emitted:

- **All**: emitted by every deployment (SaaS, self-hosted, private cloud).
- **Self-Hosted**: emitted only by self-hosted and private cloud deployments.
- **SaaS**: emitted only by SaaS (`app.flagsmith.com`).

### `FEATURE`

| Event | `log` template | Deployment |
| --- | --- | --- |
| Flag / remote config created | `New Flag / Remote Config created: <name>` | All |
| Flag / remote config updated | `Flag / Remote Config updated: <name>` | All |
| Flag / remote config deleted | `Flag / Remote Config Deleted: <name>` | All |
| Multivariate option added | `Multivariate option added to feature '<name>'.` | All |
| Multivariate option removed | `Multivariate option removed from feature '<name>'.` | All |
| Segment overrides re-ordered | `Segment overrides re-ordered for feature '<name>'.` | All |

### `FEATURE_STATE`

| Event | `log` template | Deployment |
| --- | --- | --- |
| Flag state updated | `Flag state updated for feature: <name>` | All |
| Remote config value updated | `Remote config value updated for feature: <name>` | All |
| Update scheduled | `Flag state / Remote Config value update scheduled for <datetime> for feature: <name>` | All |
| Scheduled for update by change request | `Flag state for feature '<name>' scheduled for update by Change Request '<title>' at <datetime>.` | All |
| Updated by change request | `Flag state / Remote config updated for feature: <name> by Change Request: <title>` | All |
| Scheduled change went live | `Scheduled change to Flag state / Remote config value went live for feature: <name> by Change Request: <title>` | All |
| Identity override scheduled | `Identity override scheduled for <datetime> for feature '<name>' and identity '<identifier>'` | Self-Hosted |
| Identity override created or updated | `Flag state / Remote config value updated for feature '<name>' and identity '<identifier>'` | Self-Hosted |
| Identity override value updated | `Remote config value updated for identity override on feature '<name>' and identity '<identifier>'.` | Self-Hosted |
| Identity override deleted | `Flag state / Remote config value deleted for feature '<name>' and identity '<identifier>'` | Self-Hosted |
| Segment override scheduled | `Segment override scheduled for <datetime> for feature '<name>' and segment '<segment>'` | All |
| Segment override created or updated | `Flag state / Remote config value updated for feature '<name>' and segment '<segment>'` | All |
| Segment override value updated | `Remote config updated for segment override on feature '<name>' and segment '<segment>'.` | All |
| Segment override deleted | `Flag state / Remote config value deleted for feature '<name>' and segment '<segment>'` | All |

### `SEGMENT`

| Event | `log` template | Deployment |
| --- | --- | --- |
| Segment created | `New Segment created: <name>` | All |
| Segment updated | `Segment updated: <name>` | All |
| Segment deleted | `Segment deleted: <name>` | All |

### `ENVIRONMENT`

| Event | `log` template | Deployment |
| --- | --- | --- |
| Environment created | `New Environment created: <name>` | All |
| Environment updated | `Environment updated: <name>` | All |

### `CHANGE_REQUEST`

| Event | `log` template | Deployment |
| --- | --- | --- |
| Change request created | `Change Request: <title> created` | All |
| Change request approved | `Change Request: <title> approved` | All |
| Change request committed | `Change Request: <title> committed` | All |
| Change request deleted | `Change Request: <title> deleted` | All |

### `EF_VERSION`

Emitted on environments with [Feature Versioning v2](/managing-flags/feature-versioning) enabled. Per-feature-state
changes are recorded as a single per-version entry rather than one entry per changed feature state.
Identity-override changes still emit individual records with `related_object_type: FEATURE_STATE`.

| Event | `log` template | Deployment |
| --- | --- | --- |
| New version published | `New version published for feature: <name>` | All |

### `EDGE_IDENTITY`

Edge identity overrides emit one audit log record per affected feature, with `change_type` determining which template is used.

| Event | `log` template | Deployment |
| --- | --- | --- |
| Feature override created | `Feature override created for feature '<name>' and identity '<identifier>'` | SaaS |
| Feature override updated | `Feature override updated for feature '<name>' and identity '<identifier>'` | SaaS |
| Feature override deleted | `Feature override deleted for feature '<name>' and identity '<identifier>'` | SaaS |

### `IMPORT_REQUEST`

Emitted when a customer triggers an import from a third-party provider (currently LaunchDarkly).

| Event | `log` template | Deployment |
| --- | --- | --- |
| Import requested | `New LaunchDarkly import requested` | All |
| Import succeeded | `LaunchDarkly import completed successfully` | All |
| Import failed (with error detail) | `LaunchDarkly import failed with errors:` followed by a list of `- <error>` lines | All |
| Import failed (no error detail) | `LaunchDarkly import failed` | All |

### `FEATURE_HEALTH`

See [Feature Health Metrics](/managing-flags/feature-health-metrics) for an overview of the feature and how to
configure providers.

| Event | `log` template | Deployment |
| --- | --- | --- |
| Health provider added | `Health provider <name> set up for project <project>.` | All |
| Health provider removed | `Health provider <name> removed from project <project>.` | All |
| Status changed (project-wide) | `Health status changed to <status> for feature <name>.` | All |
| Status changed (environment-scoped) | `Health status changed to <status> for feature <name> in environment <env>.` | All |

Status-change records may include additional context in the `log` field. When the event came from a third-party
provider, the provider name is appended; when the provider supplied a reason, that reason is appended too. The full
`log` then has the shape:

```
Health status changed to <status> for feature <name> in environment <env>.

Provided by <provider>

Reason:
<reason>
```
