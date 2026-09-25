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

Audit log events are sent to your webhook URL as they occur, except for [`EDGE_IDENTITY`](#edge_identity) records.

### Audit Log Webhook Payload

Flagsmith will send a `POST` request to your webhook URL with the following payload in the body:

```json
{
 "data": {
  "id": 1234,
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
  "related_object_type": "FEATURE",
  "is_system_event": false
 },
 "event_type": "AUDIT_LOG_CREATED"
}
```

`data` has the same shape as an audit log record returned by the Management API. The `author`, `environment` and
`project` objects are shortened in the example above.

`environment` is `null` for records that are not tied to a single environment, such as creating a flag. `author` is
`null` when no Flagsmith user made the change, for example when it was made with an Organisation API key or when a
scheduled change goes live. `is_system_event` is `true` for the records Flagsmith creates when it applies a change
request (see [`FEATURE_STATE`](#feature_state)).

`related_object_type` identifies the kind of resource the record is about. See [Related Object Types](#related-object-types)
for the possible values.

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

| Value                  | Description                    |
| ---------------------- | ------------------------------ |
| `FEATURE`              | Feature (flag / remote config) |
| `FEATURE_STATE`        | Feature state                  |
| `SEGMENT`              | Segment                        |
| `ENVIRONMENT`          | Environment                    |
| `CHANGE_REQUEST`       | Change request                 |
| `EDGE_IDENTITY`        | Edge identity                  |
| `IMPORT_REQUEST`       | Import request                 |
| `EF_VERSION`           | Environment feature version    |
| `FEATURE_HEALTH`       | Feature health status          |
| `RELEASE_PIPELINE`     | Release pipeline               |
| `WAREHOUSE_CONNECTION` | Warehouse connection           |
| `EXPERIMENT`           | Experiment                     |
| `METRIC`               | Metric                         |

## Audit Log Event Types

Each record carries a `related_object_type` and a `log` string. The tables below list the events Flagsmith records,
grouped by `related_object_type`. Placeholders in angle brackets (e.g. `<name>`, `<identifier>`, `<datetime>`) are
substituted with the affected resource's values at the time of the event.

The Deployment column indicates where each event is emitted:

- **All**: emitted by every deployment (SaaS, self-hosted, private cloud) where the feature is available.
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
| Segment override deleted | `Flag state / Remote config value deleted for feature '<name>' and segment '<segment>'` | All |

### `FEATURE_STATE`

| Event | `log` template | Deployment |
| --- | --- | --- |
| Flag created (one record per environment) | `New Flag / Remote Config created: <name>` | All |
| Flag state updated | `Flag state updated for feature: <name>` | All |
| Remote config value updated | `Remote config value updated for feature: <name>` | All |
| Multivariate value changed | `Multivariate value changed for feature '<name>'.` | All |
| Flag deleted (one record per environment) | `Flag / Remote Config Deleted: <name>` | All |
| Update scheduled | `Flag state / Remote Config value update scheduled for <datetime> for feature: <name>` | All |
| Scheduled for update by change request | `Flag state for feature '<name>' scheduled for update by Change Request '<title>' at <datetime>.` | All |
| Updated by change request | `Flag state / Remote config updated for feature: <name> by Change Request: <title>` | All |
| Scheduled change went live | `Scheduled change to Flag state / Remote config value went live for feature: <name> by Change Request: <title>` | All |
| Updated by release pipeline | `Flag state / Remote config updated for feature: <name> by Release pipeline: <pipeline> (stage: <stage>)` | All |
| Identity override scheduled | `Identity override scheduled for <datetime> for feature '<name>' and identity '<identifier>'` | Self-Hosted |
| Identity override created or updated | `Flag state / Remote config value updated for feature '<name>' and identity '<identifier>'` | Self-Hosted |
| Identity override value updated | `Remote config value updated for identity override on feature '<name>' and identity '<identifier>'.` | Self-Hosted |
| Identity override multivariate value changed | `Multivariate value changed for feature '<name>' and identity '<identifier>'.` | Self-Hosted |
| Identity override deleted | `Flag state / Remote config value deleted for feature '<name>' and identity '<identifier>'` | Self-Hosted |
| Segment override scheduled | `Segment override scheduled for <datetime> for feature '<name>' and segment '<segment>'` | All |
| Segment override created or updated | `Flag state / Remote config value updated for feature '<name>' and segment '<segment>'` | All |
| Segment override value updated | `Remote config updated for segment override on feature '<name>' and segment '<segment>'.` | All |
| Segment override multivariate value changed | `Multivariate value changed for feature '<name>' and segment '<segment>'.` | All |

The "Updated by change request" and "Scheduled change went live" records are system events: they have no `author` and
`is_system_event` is `true`.

Multivariate value records set `related_object_id` to the feature's ID rather than the feature state's ID.

### `SEGMENT`

| Event | `log` template | Deployment |
| --- | --- | --- |
| Segment created | `New Segment created: <name>` | All |
| Segment created by cohort sync | `New Segment created: <name> (via <source> cohort sync)` | All |
| Segment updated | `Segment updated: <name>` | All |
| Segment deleted | `Segment deleted: <name>` | All |

`<source>` is `Amplitude` or `Mixpanel`. See [Cohort Synchronisation](/third-party-integrations/cohort-synchronisation)
for an overview of the feature.

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

Emitted on environments with [Feature Versioning v2](/managing-flags/feature-versioning) enabled. On these environments,
changes to environment defaults and segment overrides, including deleting and re-ordering segment overrides, are
recorded as a single record per published version rather than as individual `FEATURE` and `FEATURE_STATE` records.
Flag changes applied by a release pipeline stage are the exception: they also create an "Updated by release pipeline"
`FEATURE_STATE` record. Identity overrides are not versioned, so identity override changes are still recorded as
described under [`FEATURE_STATE`](#feature_state) (self-hosted) or [`EDGE_IDENTITY`](#edge_identity) (SaaS).

| Event | `log` template | Deployment |
| --- | --- | --- |
| New version published | `New version published for feature: <name>` | All |

### `EDGE_IDENTITY`

Flagsmith creates one record for each feature override that changes. A single request that changes overrides for
several features creates one record per feature.

These records are shown in the Audit Log in the Flagsmith application, but are not sent to Audit Log Webhooks.

| Event | `log` template | Deployment |
| --- | --- | --- |
| Feature override created | `Feature override created for feature '<name>' and identity '<identifier>'` | SaaS |
| Feature override updated | `Feature override updated for feature '<name>' and identity '<identifier>'` | SaaS |
| Feature override deleted | `Feature override deleted for feature '<name>' and identity '<identifier>'` | SaaS |

### `IMPORT_REQUEST`

Emitted when a user imports a project from LaunchDarkly.

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
| Unhealthy status dismissed (project-wide) | `Health status changed to HEALTHY for feature <name>.` | All |
| Unhealthy status dismissed (environment-scoped) | `Health status changed to HEALTHY for feature <name> in environment <env>.` | All |

Health status changes reported by a provider are not recorded in the Audit Log. A status change record is only created
when a user dismisses an unhealthy status, which sets it back to `HEALTHY`. The provider name and the dismissal reason
are appended to the `log`, so the full `log` has the shape:

```text
Health status changed to HEALTHY for feature <name> in environment <env>.

Provided by <provider>

Reason:
<reason>
```

`<reason>` is a JSON-encoded string, for example
`{"text_blocks": [{"text": "Manually dismissed by user@domain.com"}], "url_blocks": []}`.

### `RELEASE_PIPELINE`

See [Release Pipelines](/managing-flags/release-pipeline) for an overview of the feature.

| Event | `log` template | Deployment |
| --- | --- | --- |
| Release pipeline created | `Release Pipeline: <name> created` | All |
| Release pipeline updated | `Release Pipeline: <name> updated` | All |
| Release pipeline cloned | `Release Pipeline: <name> cloned` | All |
| Release pipeline published | `Release Pipeline: <name> published` | All |
| Release pipeline converted to draft | `Release Pipeline: <name> Converted to Draft` | All |
| Release pipeline deleted | `Release Pipeline: <name> deleted` | All |
| Feature added to pipeline | `Feature: <feature> added to Release Pipeline: <name>` | All |
| Feature removed from pipeline | `Feature: <feature> removed from Release Pipeline: <name>` | All |
| Phased rollout created | `Phased rollout created for feature: <feature> by release pipeline: <name> (stage: <stage>)` | All |
| Phased rollout split changed | `Phased rollout split changed from '<old>%' to '<new>%' for feature '<feature>' by release pipeline '<name>' (stage: '<stage>')` | All |

For a cloned pipeline, `<name>` is the name of the pipeline that was cloned. Flag changes made by a pipeline stage are
recorded as `FEATURE_STATE` records (see "Updated by release pipeline" under [`FEATURE_STATE`](#feature_state)).

### `WAREHOUSE_CONNECTION`

| Event | `log` template | Deployment |
| --- | --- | --- |
| Warehouse connection created | `Warehouse connection created for environment <env>` | All |
| Warehouse connection updated | `Warehouse connection updated for environment <env>` | All |
| Warehouse connection deleted | `Warehouse connection deleted for environment <env>` | All |

### `EXPERIMENT`

See [Experimentation](/experimentation/) for an overview of the feature.

| Event | `log` template | Deployment |
| --- | --- | --- |
| Experiment created | `Experiment '<name>' created for environment <env>` | All |
| Experiment updated | `Experiment '<name>' updated for environment <env>` | All |
| Experiment deleted | `Experiment '<name>' deleted for environment <env>` | All |
| Experiment status changed | `Experiment '<name>' <status> for environment <env>` | All |
| Experiment rollout applied | `Experiment '<name>' rollout set to <percentage>% of <audience>` | All |

Status changes reuse the same template with the new status substituted for the action, so `<status>` is one of
`running`, `paused`, or `completed`. Update events are only recorded when at least one field actually changed.

`<audience>` is `all identities`, or `segments [<segment IDs>] (any)` or `segments [<segment IDs>] (all)` when the
rollout is limited to segments.

### `METRIC`

| Event | `log` template | Deployment |
| --- | --- | --- |
| Metric created | `Metric '<name>' created` | All |
| Metric updated | `Metric '<name>' updated` | All |
| Metric deleted | `Metric '<name>' deleted` | All |

Update events are only recorded when at least one field actually changed.
