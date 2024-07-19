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

:::info

When we say _rate limit_ in this document we mean to-the-second limits on API usage.

When we say _plan limit_ in this document we mean the month to month usage limit defined as part of your plan.

:::

### SDK Limits

Requests made by our SDKs are _not_ rate limited, by design; we can't predict what sort of profile your traffic will
look like.

There are scenarios where we will block your API calls, based on the _plan limit_ you are signed up to, which are
detailed below. You will be notified and given warning in the event that we are going to stop serving your flags on
account of you going over these _plan limits_.

#### Free Plan Limits

If you are on our Free Plan, we will stop answering requests from our API if you go over your
[Free Plan limit](https://www.flagsmith.com/pricing). We will send you a warning email 7 days before we block your
requests, to give you time to upgrade your account.

This block is cleared 30 days after the warning email was first sent, or when you upgrade to a paid plan.

#### Paid Plan Limits

##### If you go over your plan limit by a factor of 2 or less

If you go over your paid plan limit we will email you and give you a 30 day grace period. We will then charge you an
overage for that calendar month (or the contracted overage rate if specified in your Enterprise agreement). Please refer
to our [Pricing Page](https://www.flagsmith.com/pricing) for overage pricing.

##### If you go over your plan limit by a factor of more than 2

We will bill you for all overage above your plan in the current calendar month. You will be charged for the overage at
the end of your billing period.

### Admin API Rate Limit

Requests made to [Admin API endpoints](/clients/rest#private-admin-api-endpoints) (i.e., non-SDK endpoints) are subject
to a default rate limit of 500 requests per minute.

If you are self-hosting, you have the flexibility to modify this limit by adjusting the value of the environment
variable `USER_THROTTLE_RATE`.
