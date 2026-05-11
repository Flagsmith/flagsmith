---
title: Feature Versioning
sidebar_label: Feature Versioning
sidebar_position: 5
---

Feature Versioning records each published change to a flag as a version of that flag in an environment. You can browse the history of a flag, review which version is currently live, schedule a future version, and roll back by publishing an earlier one. It is also the foundation that [Release Pipelines](/managing-flags/release-pipeline) and segment-override diffs in [Change Requests](/administration-and-security/governance-and-compliance/change-requests) build on.

This page explains what changes when you enable Feature Versioning v2 on an environment — for your dashboard users, your webhook consumers, your audit-log pipeline, and your scripts that talk to the Admin API.

## Prerequisites

- Feature Versioning v2 is enabled per environment, in **Environment Settings → Feature Versioning**.
- You must be an **environment admin** (or a project / organisation admin) to flip the toggle.

:::caution

Enabling Feature Versioning v2 on an environment is irreversible. You cannot return an environment to v1 once the migration has run. To "roll back" a flag value, publish a new version of that flag with the earlier value.

:::

---

## What changes when you enable it

### 1. Editing a flag through the API

To produce a new published version on a v2 environment, use one of:

- **The experimental [update-flag endpoints](/integrating-with-flagsmith/flagsmith-api-overview/admin-api/updating-flags)** (`update-flag-v1`, `update-flag-v2`, `delete-segment-override`). These accept the same payloads as on v1 environments and publish a new version per call on v2 environments.
- **The new versioning endpoint family** — gives you explicit control to compose multiple changes into a single published version, or to read flag history programmatically:
  - `GET /environments/{env}/features/{feature}/versions/` — list versions for a feature.
  - `POST /environments/{env}/features/{feature}/versions/` — create a draft version.
  - `POST /environments/{env}/features/{feature}/versions/{uuid}/publish/` — publish a draft.
  - `GET /environments/{env}/features/{feature}/versions/{uuid}/featurestates/` — list the feature states inside a version.
  - `GET /environment-feature-versions/{uuid}/` — retrieve a single version by UUID.

:::caution

The legacy `POST` / `PUT` / `PATCH` endpoints on `/environments/{api_key}/featurestates/` are intended for v1 environments. On a v2 environment they mutate the live feature state in place and do **not** create a new version. If your automation calls them on a v2 environment, switch to one of the paths above.

:::

### 2. Webhooks

The shape of `FLAG_UPDATED` events does not change, but the cadence and the event mix do.

- A new event type, `NEW_VERSION_PUBLISHED`, fires once per published version. The payload contains the version UUID, the feature, the `published_by` user (or API key), and the list of feature states in the version. Add this event to your consumer's schema if you want to know when a version is published.
- `FLAG_UPDATED` continues to fire on each changed feature state. Where v1 fires once per save, v2 fires once per *changed* feature state inside the new version, alongside the `NEW_VERSION_PUBLISHED` summary. A single published version that changes the environment default plus three segment overrides triggers four `FLAG_UPDATED` events (per destination, see below) plus one `NEW_VERSION_PUBLISHED`.
- Scheduled changes deliver their webhooks at the scheduled `live_from`, not at change-request commit time.

:::info

`FLAG_UPDATED` is delivered to both environment webhooks and organisation webhooks. `NEW_VERSION_PUBLISHED` is delivered to environment webhooks only — organisation webhooks do not receive the per-version summary.

:::

### 3. Audit log

The shape of audit entries for flag edits changes.

| Field | v1 environment | v2 environment |
| --- | --- | --- |
| `related_object_type` | `FEATURE_STATE` | `EF_VERSION` |
| `related_object_id` | `FeatureState` id | `null` |
| `related_object_uuid` | `null` | The version UUID |
| `log` (message text) | `Flag state updated for feature: <name>` and variants | `New version published for feature: <name>` |
| Rows per change request | One per changed feature state | One per published version |

Identity-override edits keep the v1 shape — they remain `FEATURE_STATE`-typed regardless of whether the environment is on v2.

If you ingest the audit log into your own systems:

- Update parsers to handle `EF_VERSION` as a valid `related_object_type`.
- Read the version UUID from `related_object_uuid` rather than `related_object_id`.
- Expect the volume of rows for flag changes to drop. A change request that touched ten feature states across two features produces two `EF_VERSION` audit entries on v2 — one per feature, regardless of how many feature states inside each feature were changed.

The same change applies to the [Audit Log Webhook](/administration-and-security/governance-and-compliance/audit-logs#audit-log-webhooks).

### 4. Change requests

Change requests on a v2 environment carry their content on `change_sets` and `environment_feature_versions` rather than on `feature_states`. If your scripts read the `feature_states` array off a change-request payload, read the new fields instead. The dashboard handles this transparently.

A new email also fires when a scheduled change request fails to publish at its scheduled time due to a conflict with a more recent change.

### 5. Plan-limit accounting

Two existing limits change how they count once Feature Versioning v2 is enabled:

- **Maximum segment overrides per environment** — under v1, this counts every `FeatureSegment` row. Under v2, it counts only segment overrides on the latest published version of each feature. Customers near the cap can drop under it after enabling v2.
- **Feature history visibility days** — this plan limit becomes load-bearing under v2. Versions older than the configured window are not returned by the versions list endpoint. The dashboard's History tab respects the same window.

### 6. Dashboard

The dashboard gains a few affordances on v2 environments:

- A **History** tab on each feature shows the published versions, who published them and when, and the values they contained.
- **Change Request** diffs include changes to segment overrides as well as to environment defaults.
- **Release Pipelines** can target this environment as a stage.
- The flag toggle behaviour switches from updating a single feature state to publishing a new version — invisible to dashboard users in practice.

---

## What doesn't change

- **SDK behaviour.** The environment document served to client-side and server-side SDKs is the same shape on v1 and v2. A flag that returns `true` on v1 returns `true` on v2 for the same logical state. No SDK upgrade is required.
- **Identity overrides.** Identity-scoped flag states live outside the version graph in both modes. Setting, reading and deleting identity overrides behaves identically, and identity-override audit and webhook events keep their v1 shape.
- **The flag-state evaluation rules.** Priority between environment defaults, segment overrides and identity overrides is unchanged.

---

## Migration

Migration runs per environment, in the background, when you flip the **Feature Versioning** toggle in Environment Settings. The dashboard polls the environment while the migration completes. Existing flag values are preserved — each feature in the environment gets one initial published version representing its current state at the moment of migration. Any committed scheduled changes that have not yet gone live are also preserved as future-dated versions, set to publish at their original scheduled time.

You can enable Feature Versioning v2 on a non-production environment first to verify your webhook handlers, audit pipeline and integration consumers behave as expected before rolling out to production.

---

## What's next?

- Configure environment-level [Change Requests](/administration-and-security/governance-and-compliance/change-requests) to require approval before a version is published.
- Schedule a flag change with [Scheduled Flags](/managing-flags/scheduled-flags). Under v2, the scheduled change becomes a version with a future `live_from`.
- Set up a [Release Pipeline](/managing-flags/release-pipeline) to promote versions through a chain of environments.
