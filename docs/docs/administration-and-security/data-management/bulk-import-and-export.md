---
title: Bulk Import and Export
sidebar_label: Bulk Import & Export
sidebar_position: 30
---

Flagsmith supports two levels of bulk import and export from the UI:

- **[Environment-level](#environment-level-export)**: export and import default feature states for a single environment.
  Useful for quickly copying feature values between environments or projects.
- **[Project-level](#project-level-export)**: export and import an entire project's feature configuration, including
  segments, segment overrides, and optionally identity overrides and tags. Useful for cloning a project or migrating
  between Flagsmith instances.

For exporting an entire organisation (including all projects), see
[Organisation Import and Export](organisations-import-export).

## Common concepts

### Merge strategy

When importing, you must select a merge strategy to handle entities that already exist in the target project:

- **Skip**: existing entities are left unchanged. Only new entities from the export file are created. For example, if
  you are importing ten features but two already exist, only eight will be added. This is the safest option and is best
  for organisations that want to retain their existing data.
- **Overwrite Destructive**: existing entities that match by name are deleted and recreated from the export file. **This
  affects all environments.** Only use this when every entity in the export is known to be authoritative.

### Retention

Export files are available for download for two weeks. If an export is needed for a longer period, download it and store
a local backup.

## Environment-level export

Environment-level export captures default feature states for a single environment. This is the simplest way to copy
feature values between environments or projects.

### What is exported?

We **will** export the following data:

- Flags
- Flag States (both boolean and text values)
- Multivariate values and weights

We **will not** export the following data:

- Feature-based Segments
- Segment overrides
- Flag [custom fields](/administration-and-security/governance-and-compliance/custom-fields)
- Flag Schedules
- Tags associated with Flags
- Individual and group owners associated with Flags

### Exporting

On the Export tab of the project settings page, select **Environment Export** and choose the source environment from the
drop-down list. If required, select one or more feature tags to filter the features.

By clicking the Export Features button, the feature export should quickly process and a list of processed feature
exports is available at the bottom of the page.

### Importing

On the Import tab of the project settings page, select **Environment Import**. You will find the feature import
functionality, complete with file upload at the bottom of the page.

:::caution

The target environment is the environment to inherit the features of the exported environment. All other environments
will be set to the values defined when the feature was initially created. Use with caution, especially when using the
Overwrite Destructive merge strategy.

:::

## Project-level export

<!-- TODO: confirm plan availability -->

Project-level export captures the full feature configuration for a project, including segments and overrides. This is
the recommended way to clone a project or migrate feature configuration between Flagsmith instances.

### What is exported?

Project-level export always includes the following data:

| Data                                            | Included | Notes                   |
| ----------------------------------------------- | -------- | ----------------------- |
| Features (name, type, default value)            | Always   |                         |
| Feature states per environment (enabled, value) | Always   | Current live state only |
| Multivariate options and weights                | Always   |                         |
| Segments (rules and conditions)                 | Always   |                         |
| Segment overrides per environment               | Always   |                         |
| Environment names and settings                  | Always   | See below               |

The following data can optionally be included in the export. You will be prompted to select these options in the UI:

| Data               | Default | Notes                                  |
| ------------------ | ------- | -------------------------------------- |
| Tags               | On      |                                        |
| Identity overrides | Off     | Can significantly increase export size |

:::caution

The following data is **never** included in a project-level export:

- Users, owners, and group owners
- Change requests and approvals
- Scheduled flag changes
- Version history (only the current live state is exported)
- Audit logs
- Flag analytics

:::

#### Environment settings

The following environment settings are included in the export: change request approval requirements, client trait
permissions, banner text and colour, hide disabled flags, identity composite key hashing, hide sensitive data, feature
versioning, and identity overrides in local evaluation.

Environment API keys are **not** exported — new keys are generated automatically for any environments created during
import.

### Exporting

On the Export tab of the project settings page, select **Project Export**. Choose which optional data to include, then
click Export Project.

The export runs asynchronously. Once complete, you can download the export file from the list at the bottom of the page.

:::info

Exporting requires project administrator permissions.

:::

### Importing

On the Import tab of the project settings page, select **Project Import**. Upload the export file and select the merge
strategy.

:::info

Importing requires organisation administrator permissions.

:::

When using Overwrite Destructive, segments and their overrides are treated as a single unit: if a segment is
overwritten, all of its rules, conditions, and associated feature overrides are replaced.

#### How entities are matched

All entities are matched by name across instances, not by internal ID. This means exports are portable between Flagsmith
instances. Specifically:

- Features and segments are matched by name.
- Tags are matched by label.
- Environments are matched by name. Missing environments are created with settings from the export. For existing
  environments, the Skip strategy leaves settings unchanged, while Overwrite Destructive updates settings to match the
  export.

#### Versioning

If the target project uses feature versioning, importing with the Overwrite Destructive strategy will create new feature
versions for any features that are modified. The Skip strategy does not create new versions.
