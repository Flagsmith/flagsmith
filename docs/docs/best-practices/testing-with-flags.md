---
title: Testing with Feature Flags
sidebar_label: Testing with Feature Flags
sidebar_position: 60
---

Feature flags are an invaluable tool for testing new functionality in a controlled and safe manner. They allow you to test in production-like environments, release features to specific user groups for beta testing, and run experiments to gather data before a full roll-out.

## Testing in Production

One of the most powerful uses of feature flags is the ability to test new code in your production environment before it's released to all users.

You can deploy a new feature behind a flag that is turned off by default. The code is live in production, but invisible to your users. This allows you, your team, and any other stakeholders to access and test the feature directly in the production environment. This is often called "testing in production".

This approach gives you the highest level of confidence that the feature will behave as expected when you release it, as it's being tested against live production data and infrastructure.

## Beta Programmes and User Segments

Instead of releasing a feature to everyone at once, you can use feature flags to run beta programmes with a select group of users.

By creating a [Segment](/basic-features/segments.md) of users (e.g., "beta_testers"), you can enable a new feature exclusively for them. This allows you to gather feedback from real users in a controlled way. These users can be internal employees, a dedicated group of QA testers, or a set of customers who have opted into early access.

This is particularly useful for mobile applications. If a bug is found, you can use a feature flag to remotely disable the feature for the affected app versions, giving you time to release a fix without impacting your entire user base.

## A/B and Multivariate Testing

Feature flags are the foundation for running experiments like A/B and multivariate tests. You can present different versions of a feature to different user segments simultaneously and measure which one performs better against your key metrics.

For example, you could test:
- Different button colours or text to see which drives more clicks.
- Entirely different user flows for a new feature.
- The performance impact of a new algorithm.

Flagsmith allows you to define different variations for a feature and control the percentage of users that see each one. This, combined with an analytics tool, allows you to make data-driven decisions about your product.

You can learn more in our guide to [A/B Testing](../advanced-use/ab-testing.md). 