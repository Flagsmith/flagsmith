---
title: LaunchDarkly Importer
description: Import your LaunchDarkly data into Flagsmith
sidebar_label: LaunchDarkly
sidebar_position: 10
---

# LaunchDarkly Importer

You can import your Flags and Segments from LaunchDarkly into Flagsmith.

:::caution

Flagsmith and LaunchDarkly do have differences in their product design and underlying data model. Our importer makes
sane decisions around how to migrate data but we strongly recommend you check the results of the import by hand once the
import has finished.

:::

:::caution

Import operations will overwrite existing environments and flags in your project.

:::

## Integration Setup

1. Create a LaunchDarkly Access Token. In LaunchDarkly: Account settings > Authorization > Access tokens.
2. Create a new Project within Flagsmith, then go to Project Settings > Import. Add your Token generated in step 1.
3. The import will begin immediately.

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

Multivariate values will be taken from the `variations` field of within LaunchDarkly.

Values set to serve when targeting is off will be imported as control values.
