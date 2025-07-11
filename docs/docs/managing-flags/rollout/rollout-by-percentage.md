---
title: Rollout by Percentage
sidebar_label: Rollout by Percentage
sidebar_position: 2
---

**Rollouts by Percentage** (also known as Staged Feature Rollouts) allow you to test a new feature with a small subset of your user base. If you are happy with the feature, you can increase the percentage of users that see the feature until it is available to your entire user base.

This method increases confidence in rolling out a new feature. If issues arise, you can disable the Feature Flag, thus hiding the feature within your application.

## Prerequisites

:::important

Staged Rollouts **_only_** come into effect if you are getting the Flags for a particular Identity. If you are just retrieving the flags for an Environment without passing in an Identity, your user will never be included in the "% Split" Segment.

:::

Before you begin, make sure you have:

- A feature flag created in your project.
- Your application's [Flagsmith SDK](../../sdks/) integrated and configured.
- **Identifying users in your application:** You must identify users so that percentage rollouts are evaluated per user. For example:

  ```javascript
  flagsmith.identify('user_123');
  ```

- (Optional) Any user traits you want to use for more advanced segment rules.

---

## How to Rollout by Percentage

### 1. Create a segment with a percentage split rule

- Go to the **Segments** section in the Flagsmith dashboard.
- Create a new segment.
- Add a rule defined with the **% Split** condition. Specify a value between 1 and 100 to define what percentage of your user base is included within this Segment.
- You can optionally use the **% Split** rule alongside other Segment rules.

### 2. Connect the Segment to a Feature Flag

- Go to the **Features** section and select the feature you want to roll out.
- In the environment where you want to apply the rollout, go to the **Segment Overrides** tab.
- Add the segment you created and set the desired flag state or value for users in that segment.

### 3. Save and Monitor

- Save your changes.
- Monitor the rollout. If all goes well, gradually increase the **% Split** value to roll out the feature to more users over time.
- If issues arise, you can quickly disable the feature for all users by removing the override or setting the flag to disabled.

---

## How it works

Each Identity and Segment has a unique identifier. These two pieces of data are merged, then hashed, and a floating point value between 0.0 and 1.0 is generated from this hash. This value is then evaluated against the "% Split" rule.

### An Example

For a single Identity, the following steps are performed:

1. Take the internal Segment ID and their internal Identity ID and combine them into a single string
2. Hash that string
3. Generate a float value between 0 and 1 based on that hash

For every Segment/Identity combination, a value of between 0 and 1 is generated. Due to the hashing algorithm used, there is a consistent spread of values from 0 to 1.

- If the number comes out at `0.351` for a particular Identity, and you create a Segment % split to be 30%, that Identity will **not** be included in that Segment because `0.351` is greater than `0.3` (30%).
- If you then modify the Segment to be a 40% split, the Identity **will** be in that Segment because `0.4 > 0.351`. That way you get a consistent experience as an end-user. This works because the ID of a Segment doesn't change after it has been created.
- A second Identity might have their value hash be equal to `0.94`. In that case, they would not be in the Segment with the split at either 30% or 40%.

---

## What's next

- Read the [Segments documentation](../../basic-features/segments.md) to understand how segments work and how to combine them with percentage splits.
- See how to [roll out features by user attribute](./rollout-by-attribute.md) for targeted releases.
