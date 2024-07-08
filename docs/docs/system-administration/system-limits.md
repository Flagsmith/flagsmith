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

## Overriding Limits

### SaaS

Please contact us if you want to override the current system limits.

### Self Hosted

You can modify the system limits on a per-Project basis. These limits are defined in the database against the Project.
The easiest way to modify them is with the [Django admin](/deployment/configuration/django-admin.md) interface.

## Traffic Limits

### SDK Limits

Requests made by our SDKs are _not_ rate limited, by design; we can't predict what sort of profile your traffic will
look like.

#### Free Plan Limits

If you are on our Free Plan, we will stop answering requests from our API if you go over your
[Free Plan limit](https://www.flagsmith.com/pricing). We will send you a warning email 7 days before we block your
requests, to give you time to upgrade your account.

#### Paid Plan Limits

For paid plans, we'll give you a 30 day grace period and then charge you at $50 per million API calls for a calendar
month (or the contracted overage rate if specified in your Enterprise agreement).

### Admin API Rate Limit

Requests made to [Admin API endpoints](/clients/rest#private-admin-api-endpoints) (i.e., non-SDK endpoints) are subject
to a default rate limit of 500 requests per minute.

If you are self-hosting, you have the flexibility to modify this limit by adjusting the value of the environment
variable `USER_THROTTLE_RATE`.
