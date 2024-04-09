---
title: System Limits
---

In order to ensure consistent performance, Flagsmith has the following limitations.

### Entity Counts

- **400** Features per Project
- **100** Segments per Project
- **100** Segment Overrides per Environment
- **100** Segment Rules Conditions

### Entity Data Elements

- Maximum size of a Flag String Value is **20,000 bytes**
- Maximum size of an Identity Trait Value is **2,000 bytes**

### Segment Data Elements

- Maximum size of a Segment Rule Value is **1,000 bytes**

### Admin API Rate Limit

Requests made to [Admin API endpoints](/clients/rest#private-admin-api-endpoints) (i.e., non-SDK endpoints) are subject
to a default rate limit of 500 requests per minute.

If you are self-hosting, you have the flexibility to modify this limit by adjusting the value of the environment
variable `USER_THROTTLE_RATE`.

## Overriding Limits

### SaaS

Please contact us if you want to override the current system limits.

### Self Hosted

You can modify the system limits on a per-Project basis. These limits are defined in the database against the Project.
The easiest way to modify them is with the [Django admin](/deployment/configuration/django-admin.md) interface.
