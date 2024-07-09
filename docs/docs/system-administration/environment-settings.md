---
title: Environment Settings
---

## Use Consistent Hashing

This setting allows legacy environments to manually choose to update the hashing algorithm used by the engine when
evaluating multivariate and percentage splits. Enabling this setting ensures that identities that are evaluated across
the Core API, Edge API and local evaluation mode in our server side SDKs receive the same multivariate variations and
appear in the same segments that use the percentage split operator. All new environments are created with this setting
enabled by default.

:::caution

This will result in identities receiving different variations and being evaluated in different segments (that use the %
split operator) when evaluated against the remote API. Evaluations in local evaluation mode will not be affected.

:::

## Use Metadata

When creating or updating a segment, you can enhance its information by adding previously created and enabled metadata
fields. To create and enable this you can do it in the metadata tab on the project settings page.

If you have metadata for features, it will create a list of fields that can be filled, saved, and will be stored with
the feature's save flag.

![Image](/img/metadata/metadata-environment.png)
