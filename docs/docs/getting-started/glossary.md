---
title: Glossary
sidebar_label: Glossary
sidebar_position: 3
---

This glossary provides concise definitions for some of the key concepts within Flagsmith:

- [**A/B Testing**](/advanced-use/ab-testing.md): A method of testing different feature variants with different user groups, often implemented using multivariate flags and percentage splits.

- [**Core API**](/edge-api/Overview.md#core-api): Flagsmith's private API for programmatic control of the platform.

- [**Edge API / Edge Proxy**](/advanced-use/edge-api.md): Flagsmith's publicly accessible API, specifically intended for use with our SDKs.

- [**Environment**](/basic-features/index.md#environments): Environments are a way to separate the configuration of your features. A project can have any number of environments.

- [**Environment Document**](/clients/index.md#the-environment-document): A JSON document containing all configuration for feature flags in an environment.

- [**Feature**](/basic-features/managing-features.md): A configuration that can be enabled, disabled, or set to a specific value. Features are shared across all Environments in a project, but their values/states can be modified between Environments.

- [**Feature Flag**](/basic-features/index.md): A boolean or multivariate switch to enable/disable features or set their values dynamically without deploying code.

- [**Identity**](/basic-features/managing-identities.md): An identity represents a specific user within a particular environment. Identities allow you to manage and override feature settings for individual users, and the same user can have different features enabled in different environments.

- [**Local Evaluation Mode**](/clients/index.md#local-evaluation): A mode where the SDK evaluates feature flags locally using a downloaded environment document, reducing latency and API calls.

- [**Multivariate Flag**](/basic-features/managing-features.md#multi-variate-flags): A feature flag that can take on multiple values (not just on/off), useful for A/B testing and gradual rollouts.

- [**Organisation**](/basic-features/index.md#organisations): Organisations are a way for you and other team members to manage projects and their features. Users can be members of multiple organisations.

- [**Project**](/basic-features/index.md#projects): Projects contain one or more Environments that share a single set of Features across all of the Environments within the Project. Organisations can have any number of Projects.

- [**Role-Based Access Control (RBAC)**](/system-administration/rbac.md): A system for managing user permissions and access within an organisation.

- [**SDK (Software Development Kit)**](/clients/): Client libraries provided by Flagsmith for integrating feature flagging into applications.

- [**Segment**](/basic-features/segments.md): A group of users defined by traits (e.g., logins, device, location, or custom traits). You can override feature defaults for segments, such as enabling features for a "power user" group.

- [**Staged Rollout**](/guides-and-examples/staged-feature-rollouts.md): Gradually enabling a feature for increasing percentages of users to reduce risk.

- [**Trait**](/basic-features/managing-identities.md#identity-traits): A key-value pair associated with an identity, that can store any type of data.