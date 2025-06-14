---
title: Targeting Feature Flags
---

# Targeting Feature Flags

Targeting feature flags allows you to control which users or groups receive specific features or configurations. In Flagsmith, this is typically achieved using segments, traits, and overrides.

## Staged Feature Rollouts

Staged Feature Rollouts allow you to test a new feature with a small subset of your user base. If you're happy with the feature, you can increase the percentage of users that see the feature until it's available to your entire user base.

:::important
Staged Rollouts **_only_** come into effect if you are getting the Flags for a particular Identity. If you are just retrieving the flags for an Environment without passing in an Identity, your user will never be included in the "% Split" Segment.
:::

To implement staged rollouts:
1. Create a Segment with a "% Split" condition (1-100%)
2. Connect the segment to your feature flag
3. Monitor the feature's performance
4. Adjust the percentage as needed

## How to Target Features Using Segments

### Prerequisites
- A feature flag created in your project
- Basic understanding of Flagsmith segments
- User traits configured in your application

### Steps

1. Create a Segment
   1. Navigate to **Segments** in the Flagsmith dashboard
   2. Click **Create Segment**
   3. Enter a name for your segment
   4. Add your first rule:
      - Select a trait (e.g., 'subscription_plan')
      - Choose an operator (e.g., 'Exactly Matches')
      - Enter the value (e.g., 'premium')
   5. Click **Create Segment**

2. Set Up Feature Override
   1. Go to **Features** in your environment
   2. Select the feature you want to target
   3. Click the **Segment Overrides** tab
   4. Click **Add Segment Override**
   5. Select your newly created segment
   6. Configure the feature state/value for this segment
   7. Save your changes

3. Verify Configuration
   1. Check the segment preview to see matching users
   2. Test with a user that matches the segment rules
   3. Confirm the overridden value is returned

### What to Do Next
- Monitor segment membership using analytics
- Adjust segment rules if needed
- Add additional segment overrides as required

:::note
Your application must identify users and send traits to Flagsmith for segment targeting to work.
:::

## Segment Overrides
Segment overrides allow you to control the state or value of a feature for all identities in a segment, without affecting other users.

## Example Use Cases
- Roll out a feature to 10% of users in a segment
- Enable a feature only for users on a specific plan
- Show a feature to users with a certain app version

:::tip 
For a hands-on guide to targeting feature flags, see the [Transient Traits and Identities tutorial](./transient-traits-identities.md).
:::