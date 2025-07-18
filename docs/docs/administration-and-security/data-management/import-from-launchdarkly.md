---
title: Import from LaunchDarkly
description: Migrate your flags and project from LaunchDarkly into Flagsmith
sidebar_label: Import from LaunchDarkly
sidebar_position: 20
---

# LaunchDarkly Migrator - Migrate from LaunchDarkly

This guide explains how to migrate your flags and segments from LaunchDarkly into Flagsmith.

:::caution

Flagsmith and LaunchDarkly do have differences in their product design and underlying data model. Our importer makes
sane decisions around how to migrate data but we strongly recommend you check the results of the import by hand once the
import has finished.

:::

## Prerequisites

- **LaunchDarkly Access Token**: You will need an Access Token from your LaunchDarkly account. To generate the token:
    1. Log in to your LaunchDarkly account.
    2. Navigate to **Account settings** > **Authorization** > **Access tokens**.
    3. Create a new Access Token.

## Integration Setup

:::caution

Import operations will overwrite existing environments and flags in your project.

:::

Follow these steps to set up the integration and initiate the import:

1.  Import into Flagsmith:
    - Create a new project within Flagsmith, or select an existing one.
    - Go to **Project Settings** > **Import**.
    - Paste the Access Token previously generated into the provided field.
2.  Start the import: The import process will begin immediately upon adding the token.

## What we will import

For each Project imported the importer will create a new Project in Flagsmith and copy across the following Entities.

### Environments

All of the LaunchDarkly `Environments` within the Project will be copied into Flagsmith as `Environments`

### Flags

LaunchDarkly `Flags` will be copied into Flagsmith as follows:

#### Boolean Flags

Boolean LaunchDarkly flags are imported into Flagsmith with the appropriate boolean state, with no flag value set on the Flagsmith side.

Boolean values will be taken from the `_summary -> on` field of within LaunchDarkly.

#### Multivariate Flags

Multivariate LaunchDarkly flags will be imported into Flagsmith as MultiVariate Flagsmith flag values.

Multivariate values will be taken from the `variations` field of within LaunchDarkly.

Values set to serve when targeting is off will be imported as control values.
