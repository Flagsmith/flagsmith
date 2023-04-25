---
title: Staged Feature Rollouts
---

## What are Staged Feature Rollouts

Staged Feature Rollouts allow you to test a new feature with a small subset of your user base. If you are happy with the
feature, you can increase the percentage of users that see the feature until it is available to your entire user base.

This method can increase your confidence in rolling out a new feature. If there are issues with the rollout, you can
simply disable the Feature Flag, thus hiding the feature within your application.

## Creating Staged Rollouts

:::important

Staged Rollouts **_only_** come into effect if you are getting the Flags for a particular Identity. If you are just
retrieving the flags for an Environment without passing in an Identity, your user will never be included in the "%
Split% Segment.

:::

You can achieve staged rollouts by creating a [Segment](/basic-features/managing-segments.md) and adding a rule defined
with the "% Split" condition. Specifying a "% Split" value between 1 and 100 then defines what percentage of your user
base are included within this Segment.

![Image](/img/percent-rollout.png)

Once you have created the Segment, you can then go ahead and connect it up to a Feature Flag as per regular
[Segments](/basic-features/managing-segments.md).

Note that you can include the "% Split" rule alongside other Segment rules if you wish.

## How does it work

Each Identity and Segment has a unique identifier. These two pieces of data are merged then hashed, and a floating point
value between 0.0 and 1.0 is generated from this hash. This value is then evaluated against the "% Split" rule.

### An Example

So to take an example. For a single Identity, we perform the following steps:

1. Take the internal Segment ID and their internal Identity ID and combine them into a single string
2. We then hash that string
3. We then generate a float value between 0 and 1 based on that hash

So for every Segment/Identity combination, a value of between 0 and 1 is generated. Due to the hashing algorithm used,
we ensure a consistent spread of values from 0 to 1.

So lets say that number comes out at 0.351 for a particular Identity. If you create a Segment % split to be 30%, that
Identity will not be included in that Segment because 0.351 is great than 0.3 (30%). If you then modify the Segment to
be a 40% split, the Identity WILL be in that Segment because 0.4 > 0.351. That way you get a consistent experience as an
end-user. This works because the ID of a Segment doesn't change after it has been created.

A second Identity might have their value hash be equal to 0.94. In that case, they would not be in the Segment with the
split at either 30% of 40%.
