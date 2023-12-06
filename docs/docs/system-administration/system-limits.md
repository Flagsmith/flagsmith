---
title: System Limits
---

## Overriding Limits

### SaaS

Please contact us if you want to override the current system limits.

### Self Hosted

You can modify the system limits on a per-Project basis. These limits are defined in the database against the Project.
The easiest way to modify them is with the [Django admin](/deployment/configuration/django-admin.md) interface.

## Current Limits

In order to ensure consistent performance, Flagsmith has the following limitations.

### Entity Counts

- **400** Features per Project
- **100** Segments per Project
- **100** Segment Overrides per Environment

### Entity Data Elements

- Maximum size of a Flag String Value is **20,000 bytes**
- Maximum size of an Identity Trait Value is **2,000 bytes**

### Segment Data Elements

- Maximum size of a Segment Rule Value is **1,000 bytes**
