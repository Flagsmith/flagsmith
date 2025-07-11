---
title: Rollout by Attribute
sidebar_label: Rollout by Attribute
sidebar_position: 1
---

This guide explains how to enable a feature for specific users based on their attributes (traits) in Flagsmith using Segments and Segment Overrides. Attributes can include user role, subscription plan, app version, or device type.

## Prerequisites

- A Flagsmith project and environment.
- A feature flag created in your project.
- Your application's [Flagsmith SDK](../../clients/index.md) integrated and configured.

## Steps

### 1. Identify and Send User Traits

Ensure your application is identifying users and sending their relevant attributes (traits) to Flagsmith. For example, you might send traits like `plan`, `email`, `platform`, or `version` using your SDK:

```javascript
flagsmith.identify('user_123');
flagsmith.setTrait('plan', 'pro');
flagsmith.setTrait('version', '5.4.1');
```

### 2. Create a Segment Based on Attribute(s)

1. Go to the **Segments** section in the Flagsmith dashboard.
2. Create a new segment and add rules that match the attribute(s) you want to target. For example:
  - `plan = pro`
  - `email Contains @yourcompany.com`
  - `version SemVer >= 5.4.0`
3. You can combine multiple rules for more precise targeting.

### 3. Apply a Segment Override to Your Feature Flag

1. In the environment where you want to apply the rollout, go to the **Features** section and select the feature you want to roll out.
2. Navigate to the **Segment Overrides** tab.
- Select the segment you created in the dropdown and set the desired flag state or value for users in that segment.
- Save your changes.

Done! Now you can test with users who match (and don’t match) the segment to ensure the feature is enabled/disabled as expected.

---

## Advanced Use Cases

- You can combine attribute rules with a **% Split** rule for staged rollouts (e.g., only 10% of "pro" users).
- You can use operators like `In`, `SemVer`, `Modulo`, etc., for more complex targeting.

---

## What's next

- Read the [Segments documentation](../../basic-features/segments.md) to understand how they work and their relationship with overrides.
- See the [Staged Feature Rollouts guide](./rollout-by-percentage.md) to combine attribute rules with percentage-based rollouts for gradual releases.
- Understand [Managing Identities](../../basic-features/managing-identities.md) to ensure consistent user identification and attribute management across your application.
