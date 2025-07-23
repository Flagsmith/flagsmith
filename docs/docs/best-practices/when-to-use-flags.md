---
title: When to use Feature Flags
sidebar_label: When to use Feature Flags
sidebar_position: 20
---

Feature Flags are a powerful tool for modern software development. They allow teams to modify system behaviour without changing code and deploying new versions. But when exactly should you use them? This guide covers the common use cases for feature flags.

## Decouple Deployment from Release

The most common reason to use feature flags is to separate the act of deploying code to production from the act of releasing a feature to users.

### Feature Roll-Outs
You can deploy new features to production behind a feature flag that is turned off. The code is in production, but no users can see it. This allows you to test the feature in a production environment. Once you are confident, you can release the feature by turning the flag on. This gives you full control over the release process, independent of code deployment cycles.

### Staged Rollouts
Instead of releasing a feature to all users at once, you can do it gradually. With staged rollouts, you can release a feature to a small percentage of your users first (e.g., 1%, 10%, 50%) and monitor its performance and stability. This minimises the risk and impact of any potential issues. If something goes wrong, you can quickly turn the flag off.

## Experimentation

Feature flags are essential for running experiments like A/B tests or multivariate tests.

### A/B Testing
You can present two or more versions of a feature to different segments of users simultaneously to see which one performs better. For example, you can test different button colours, text, or user flows.

### Multivariate Testing
This is similar to A/B testing but allows you to test multiple variables at once. You can define different variations for a feature and let Flagsmith distribute users among them based on defined weightings.

## Operational Control

Feature flags can also be used as operational levers to manage your application in production.

### Kill Switches
A kill switch is a long-lived flag that allows you to quickly disable a feature or a part of your application in case of an emergency. For example, if a new feature is causing performance issues or has a critical bug, you can use a kill switch to turn it off instantly without having to roll back a deployment. This can also be used to disable parts of the application during maintenance or downtime of a dependency.

### Mobile App Versioning
For mobile applications, a fix for a bug requires a new release to be approved by app stores and then users have to update their app. This can take time. With feature flags, you can remotely disable a broken feature for affected app versions, giving you time to fix the bug and release an update.

## Personalisation and Entitlement

### Feature Management for Different User Segments
You can use feature flags to control which features are available to different groups of users. This is often used for managing features based on subscription plans (e.g., Free vs. Pro). You can create segments of users based on their attributes (like `plan: 'scale-up'`) and then enable or disable features for those segments.

### Beta Programmes
When you want to release a new feature to a specific group of beta testers, you can create a segment for them and enable the feature only for that segment. 

## Further Reading

- For a deeper dive into the different types of feature flag lifecycles, check out the [Feature Flags Lifecycles guide](./flag-lifecycle.md).
- Learn more about [A/B and multivariate testing](../advanced-use/ab-testing.md) to see how experimentation can be managed with Flagsmith.
- Explore how [Segments](../basic-features/segments.md) can help you target features to specific groups of users. 
