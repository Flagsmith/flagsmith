---
title: Glossary
sidebar_label: Glossary
sidebar_position: 3
---

This glossary provides concise definitions for some of the key concepts within Flagsmith:

- **A/B Testing**: A method of testing different feature variants with different user groups, often implemented using multivariate flags and percentage splits.

- **Core API**: Flagsmith's private API for programmatic control of the platform. 

- **Edge API / Edge Proxy**: Flagsmith's publicly accessible API, specifically intended for use with our SDKs.

- **Environment**: Environments are a way to separate the configuration of your features. A project can have any number of environments.

- **Environment Document**: A JSON document containing all configuration for feature flags in an environment.

- **Feature**: A configuration that can be enabled, disabled, or set to a specific value. Features are shared across all Environments in a project, but their values/states can be modified between Environments.

- **Feature Flag**: A boolean or multivariate switch to enable/disable features or set their values dynamically without deploying code.

- **Identity**: An identity represents a specific user within a particular environment. Identities allow you to manage and override feature settings for individual users, and the same user can have different features enabled in different environments.

- **Local Evaluation Mode**: A mode where the SDK evaluates feature flags locally using a downloaded environment document, reducing latency and API calls.

- **Multivariate Flag**: A feature flag that can take on multiple values (not just on/off), useful for A/B testing and gradual rollouts.

- **Organisation**: Organisations are a way for you and other team members to manage projects and their features. Users can be members of multiple organisations.

- **Project**: Projects contain one or more Environments that share a single set of Features across all of the Environments within the Project. Organisations can have any number of Projects.

- **Role-Based Access Control (RBAC)**: A system for managing user permissions and access within an organisation. 

- **SDK (Software Development Kit)**: Client libraries provided by Flagsmith for integrating feature flagging into applications.

- **Segment**: A group of users defined by traits (e.g., logins, device, location, or custom traits). You can override feature defaults for segments, such as enabling features for a "power user" group.

- **Staged Rollout**: Gradually enabling a feature for increasing percentages of users to reduce risk.

- **Trait**: A key-value pair associated with an identity, that can store any type of data.