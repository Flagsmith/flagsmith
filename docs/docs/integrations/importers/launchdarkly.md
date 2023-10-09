---
title: LaunchDarkly Importer
description: Import your LaunchDarkly data into Flagsmith
sidebar_label: LaunchDarkly
sidebar_position: 10
---

You can import your Flags and Segments from LaunchDarkly into Flagsmith.

## Integration Setup

1. Create a LaunchDarkly Access Token. In LaunchDarkly: Account settings > Authorization > Access tokens.
2. Using your Access Token and a LaunchDarkly project key (usually `"default"`) , create an Import Request for a
   Flagsmith project of your choice:

```bash
curl -X 'POST' \
  'https://api.flagsmith.com/api/v1/projects/<project_id>/imports/launch-darkly/' \
  -H 'content-type: application/json' \
  -H 'authorization: Token <api token>' \
  -d '{"token":"<launchdarkly token>","project_key":"default"}'
```

4. The import will begin immediately. Check the import request status:

```bash
curl https://api.flagsmith.com/api/v1/projects/<project id>/imports/launch-darkly/<import_request_id>/ \
    -H 'authorization: Token <api token>'
```

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
