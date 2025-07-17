---
title: Targeting and Rollouts
description: Conceptual overview of targeting and rollout operations for feature flags in Flagsmith.
sidebar_label: Targeting & Rollouts
---

# Targeting and Rollouts: Concepts & Overview

Flagsmith provides powerful targeting and rollout capabilities to help you deliver features safely, progressively, and with maximum control. This page explains the concepts and available operations for targeting and rollouts.

## What is Targeting?

**Targeting** is the practice of controlling feature flag states for specific users or groups, rather than for all users at once. This enables you to:
- Release features to internal users, beta testers, or select customers before a full launch.
- Target features to users with specific traits (such as geography, subscription level, device type, or application version).
- Run experiments (A/B or multivariate tests) by segmenting your user base.
- Roll out features gradually to reduce risk and monitor impact.

## What is a Rollout?

A **rollout** is a staged release of a feature to a subset of users, often increasing the percentage of users over time. Rollouts help you to:
- Minimise the impact of bugs or regressions by limiting exposure.
- Monitor performance and user feedback before a full launch.
- Quickly disable ("kill switch") a feature for affected users if issues arise.

## Targeting and Rollout Operations in Flagsmith

Flagsmith supports several operations for targeting and rollouts.

### Environment-level Flags
- Control a feature for all users in a given environment (e.g., development, staging, production).
- Useful for broad control and environment-specific testing.

### Identity Targeting
- Override feature flags for individual users ("identities").
- Enables internal testing, QA, customer support, or personalised experiences at the user level.

### Segment Targeting
- Define **segments**—groups of users matching rules based on traits (e.g., location, plan, app version, usage).
- Override feature flags for all users in a segment.
- Segments can be combined with percentage rollouts and other rules for advanced targeting.

### Staged Rollouts
- Gradually enable a feature for a percentage of users, either globally or within a segment.
- Useful for canary releases, progressive delivery, and experimentation.
- Flagsmith uses a deterministic hashing algorithm to ensure consistent user experiences during rollouts.

### Multivariate Flags
- Assign users to different flag "variants" (e.g., for A/B/n testing) based on defined weightings.
- Can be combined with targeting and rollouts for advanced experiments and optimisation.

## Why Use Targeting and Rollouts?

- **Reduce risk:** Catch issues early by exposing new features to a small group first.
- **Personalise experiences:** Deliver features to users who will benefit most.
- **Experiment and optimise:** Test multiple variants and measure impact.
- **Comply with requirements:** Target features to specific regions, plans, or device types.
- **Respond quickly:** Instantly disable features for affected users if problems arise.

## Learn More

- [Managing Identities](/basic-features/managing-identities.md)
- [Segments & Segment Targeting](/basic-features/segments.md)
- [Staged Feature Rollouts](/guides-and-examples/staged-feature-rollouts.md)
- [A/B and Multivariate Testing](/advanced-use/ab-testing.md)
- [Managing Features & Multivariate Flags](/basic-features/managing-features.md)
