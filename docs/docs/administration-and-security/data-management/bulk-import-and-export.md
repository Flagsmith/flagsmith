---
title: Bulk Import and Export
sidebar_label: Bulk Import & Export
sidebar_position: 30
---

The bulk import and export of feature data associated with a given environment is possible in Flagsmith. The feature data that is exported includes multivariate features, but does not include other data such as tags, owners, group owners, etc. This functionality is useful for transferring features between any running instances of Flagsmith, even when only a subset of features (for example, importing features of a given tag) is needed.

## What is exported?

We **will** export the following data:

- Flags
- Flag States (both boolean and text values)
- Multivariate values and weights

We **will not** export the following data:

- Feature-based Segments
- Segment overrides
- Flag [custom fields](/advanced-use/custom-fields.md)
- Flag Schedules
- Tags associated with Flags
- Individual and group owners associated with Flags

## Exporting

On the Export tab of the project settings page, it is possible to export the project's features using the environment's values. Simply select the source environment from the drop-down list and, if required, select one or more feature tags to filter the features.

By clicking the Export Features button, the feature export should quickly process and a list of processed feature exports is available at the bottom of the page.

:::tip
Feature exports are available for only two weeks, so if an export is needed for a longer period, be sure to make a local backup.
:::

## Importing

On the Import tab of the project settings page, you will find the feature import functionality, complete with file upload at the bottom of the page.

:::caution
The target environment is the environment to inherit the features of the exported environment. All other environments will be set to the values defined when the feature was initially created. Use with caution, especially when using the Overwrite Destructive merge strategy.
:::

### Merge Strategy

Since a feature may have an identical name, it is important to carefully select a merge strategy during a feature import.

The first option is the Skip strategy, which allows an import to process a feature export and, at any time a feature has a pre-existing feature present, it skips the import for that given feature. For example, if you are importing ten features but two of them were already there, only eight features will be added to the project. This strategy is best for organisations that want to retain their existing data as closely as possible.

The second option is the Overwrite Destructive strategy. In contrast to the Skip strategy, the Overwrite Destructive method overwrites your existing features, and it is important to remember that this is across all environments. This strategy is most useful only when every feature that was included in the export was vetted to be authoritative in the target project. 