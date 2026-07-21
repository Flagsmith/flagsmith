---
title: Feature Versioning
sidebar_label: Feature Versioning
sidebar_position: 5
---

Feature Versioning attaches versions to feature value and segment override updates. You can browse past versions, schedule future ones, and roll back to an earlier version.

Editing flags through the dashboard is unchanged. This page describes what changes when you enable Feature Versioning v2 on an environment for your webhook consumers, your audit-log pipeline, and your scripts that talk to the Admin API.

## Prerequisites

- Feature Versioning v2 is enabled per environment, in **Environment Settings → Feature Versioning**.
- You must be an **environment admin** (or a project / organisation admin) to flip the toggle.

:::caution

Enabling Feature Versioning v2 on an environment is irreversible.

:::

---

## What changes when you enable it

### 1. Editing a flag through the API

To produce a new published version on a v2 environment, use one of:

- **The experimental [update-flag endpoints](/integrating-with-flagsmith/flagsmith-api-overview/admin-api/updating-flags)** (`update-flag-v1`, `update-flag-v2`, `delete-segment-override`). These accept the same payloads as on v1 environments and publish a new version per call on v2 environments.
- **The new versioning endpoint family**:
  - `GET /environments/{env}/features/{feature}/versions/` — list versions for a feature.
  - `POST /environments/{env}/features/{feature}/versions/` — create a draft version.
  - `POST /environments/{env}/features/{feature}/versions/{uuid}/publish/` — publish a draft.
  - `GET /environments/{env}/features/{feature}/versions/{uuid}/featurestates/` — list the feature states inside a version.
  - `GET /environment-feature-versions/{uuid}/` — retrieve a single version by UUID.

:::caution

The legacy `POST` / `PUT` / `PATCH` endpoints on `/environments/{api_key}/featurestates/` return `400 Bad Request` on environments with Feature Versioning enabled. Use one of the paths above instead.

:::

### 2. Webhooks

The shape of `FLAG_UPDATED` events does not change, but the cadence and the event mix do.

- A new event type, `NEW_VERSION_PUBLISHED`, fires once per published version. The payload contains the version UUID, the feature, the `published_by` user (or API key), and the list of feature states in the version.
- `FLAG_UPDATED` continues to fire on each changed feature state. Where v1 fires once per save, v2 fires once per *changed* feature state inside the new version, alongside the `NEW_VERSION_PUBLISHED` summary. A single published version that changes the environment default plus three segment overrides triggers four `FLAG_UPDATED` events (per destination, see below) plus one `NEW_VERSION_PUBLISHED`.
- Scheduled changes deliver their webhooks at the scheduled `live_from`, not at change-request commit time.

:::info

`FLAG_UPDATED` is delivered to both environment webhooks and organisation webhooks. `NEW_VERSION_PUBLISHED` is delivered to environment webhooks only — organisation webhooks do not receive the per-version summary.

:::

### 3. Audit log and Audit Log Webhooks

The shape of audit entries for flag edits changes. Entries delivered via [Audit Log Webhooks](/administration-and-security/governance-and-compliance/audit-logs#audit-log-webhooks) carry the same change.

| Field | v1 environment | v2 environment |
| --- | --- | --- |
| `related_object_type` | `FEATURE_STATE` | `EF_VERSION` |
| `related_object_id` | `FeatureState` id | `null` |
| `related_object_uuid` | `null` | The version UUID |
| `log` (message text) | `Flag state updated for feature: <name>` and variants | `New version published for feature: <name>` |
| Webhook calls per change request | One per changed feature state | One per published version |

Identity-override edits keep the v1 shape — they remain `FEATURE_STATE`-typed regardless of whether the environment is on v2.

If you have an Audit Log Webhook configured:

- Update your handler to accept `EF_VERSION` as a valid `related_object_type`.
- Read the version UUID from `related_object_uuid`; `related_object_id` is `null` on these entries.

### 4. Change requests

**API Changes**: change requests on a v2 environment carry their content on `change_sets` and `environment_feature_versions` rather than on `feature_states`. If your scripts read the `feature_states` array off a change-request payload, read the new fields instead.

**Functionality-wise**, v2 also enables using Change Requests to gate **segment override** changes — otherwise it only covers changes to environment default.

Additionally, a new email also fires when a scheduled change request fails to publish at its scheduled time due to a conflict with a more recent change.

---

## Migration

Migration runs per environment, in the background, when you flip the **Feature Versioning** toggle in Environment Settings. The dashboard polls the environment while the migration completes. Existing flag values are preserved — each feature in the environment gets one initial published version representing its current state at the moment of migration. Any committed scheduled changes that have not yet gone live are also preserved as future-dated versions, set to publish at their original scheduled time.
