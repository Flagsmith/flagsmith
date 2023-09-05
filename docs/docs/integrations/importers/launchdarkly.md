---
title: LaunchDarkly Importer
description: Import your LaunchDarkly data into Flagsmith
sidebar_label: LaunchDarkly
sidebar_position: 10
---

You can import your Flags and Segments from LaunchDarkly into Flagsmith.

## Integration Setup

1. Create a LaunchDarkly Access Token. In LaunchDarkly: Account settings > Authorization > Access tokens.
2. From the Flagsmith Integrations menu, select LaunchDarkly. Paste the Access Token from step #1 above.
3. Start the import.

## What we will import

For each Project imported the importer will create a new Project in Flagsmith and copy across the following Entities.

### Environments

All of the LaunchDarkly `Environments` within the Project will be copied into Flagsmith as `Environments`

### Flags

LaunchDarkly `Flags` will be copied into Flagsmith.

#### Boolean Flags

Boolean LaunchDarkly flags are imported into Flagsmith with the appropriate boolean state, with no flag value set on the
Flagsmith side.

Boolean values will be taken from the `_summary -> on` field of within LaunchDarkly.

#### Multivariate Flags

Multivariate LaunchDarkly flags will be imported into Flagsmith as MultiVariate Flagsmith flag values.

Multivariate values will be taken from the `Multivariate` (#todo: check this) field of within LaunchDarkly.
