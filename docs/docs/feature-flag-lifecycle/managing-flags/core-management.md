---
title: How to Manage Feature Flags
description: Step-by-step guide to creating, editing, cloning, and deleting feature flags
---

# How to Manage Feature Flags

This guide walks you through the essential operations for managing feature flags in Flagsmith. Learn how to create, modify, clone, and safely remove flags from your projects.

## Creating a New Feature Flag

To create a new feature flag:
1. Go to the Flags page within any Environment.
2. Click the **Create Feature** button.
3. Fill in the flag details and save.

### Flag Types
- **Boolean**: On (true) or Off (false). Used for simple feature toggles.
- **String/Integer**: Store and override values as needed. Useful for configuration values.
- **Multivariate**: Select from a predefined list of values for A/B testing or advanced use cases.

### Default Settings
By default, when you create a feature with a value and enabled state, it acts as a default for your other Environments. You can prevent this behavior:

1. Go to Project Settings
2. Enable 'Prevent flag defaults'
3. New features will start disabled with empty values in all environments

:::tip
The maximum size of each String Value is **_20,000 bytes_**.
:::

## Managing Flags

### Editing and Cloning
- **Edit**: Update flag name, description, or values
- **Clone**: Duplicate flags to reuse configurations
- **Archive**: Hide unused flags without deleting them
- **Server-Side Only**: Prevent flags from being returned to client-side SDKs

### Multivariate Flags
Multivariate flags define multiple possible values with assigned weightings:

- **Control**: The default value when not targeting specific identities
- **Variations**: Alternative values with percentage-based distribution
- **Weights**: Set per environment for flexible testing

:::important
The Control and Variant weightings **_only_** come into effect if you are getting the Flags for a particular Identity.
If you are just retrieving the flags for an Environment without passing in an Identity, you will **_always_** receive
the Control value.
:::

### Flag Owners
For larger teams:
- Assign owners to individual flags
- Track responsibility and ownership
- Facilitate communication about flag changes

### Flag Naming and Case Sensitivity
By default, Flagsmith stores flags in lowercase to minimize errors. You can:
- Enable case-sensitive flags in Project Settings
- Set regular expressions to enforce naming conventions

:::tip
We don't recommend making flags case sensitive as it can lead to runtime errors.
:::

## Best Practices

### General Guidelines
- Remove short-lived flags from both codebase and Flagsmith when done
- Use long-lived flags for kill switches or ongoing management
- Document flag purposes and ownership

### Mobile Applications
- Keep kill switches available for quick feature disabling
- Consider archiving over deleting flags used by older app versions
- Use staged rollouts for gradual feature introduction

### Cleanup and Maintenance
- Regularly review and remove unused short-lived flags
- Archive flags instead of deleting if uncertain
- Maintain documentation of flag purposes

For more on custom fields, see [Custom Fields](/advanced-use/custom-fields).