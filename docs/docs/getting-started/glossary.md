---
title: Glossary
sidebar_label: Glossary
sidebar_position: 3
---

This glossary provides concise definitions for some of the key concepts within Flagsmith:

- [**A/B Testing**](/experimentation-ab-testing): A method of testing different feature variants with different user groups, often implemented using multivariate flags and percentage splits.

- [**Core API**](/edge-api/overview): Flagsmith's private API for programmatic control of the platform.

- [**Edge API**](/performance/edge-api): Flagsmith's publicly accessible API, specifically intended for use with our SDKs.

- [**Edge Proxy**](/performance/edge-proxy): A self-hosted service that provides a local, low-latency interface to the Flagsmith API.

- [**Environment**](/flagsmith-concepts/data-model#environments): Environments are a way to separate the configuration of your features. A project can have any number of environments.

- [**Environment Document**](/integrating-with-flagsmith/integration-overview): A JSON document containing all configuration for feature flags in an environment.

- [**Feature**](/flagsmith-concepts/data-model#features): A configuration that can be enabled, disabled, or set to a specific value. Features are shared across all Environments in a project, but their values/states can be modified between Environments.

- [**Feature Flag**](/getting-started/feature-flags): A boolean or multivariate switch to enable/disable features or set their values dynamically without deploying code.

- [**Identity**](/flagsmith-concepts/data-model#identities): An entity within a particular environment, against which you can manage and override feature settings.

- [**Local Evaluation Mode**](/integrating-with-flagsmith/integration-overview): A mode where the SDK evaluates feature flags locally using a downloaded environment document, reducing latency and API calls.

- [**Multivariate Flag**](/managing-flags/core-management): A feature flag that can take on multiple values (not just on/off), useful for A/B testing.

- [**Organisation**](/flagsmith-concepts/data-model#organisations): Organisations are a way for you and other team members to manage projects and their features. Users can be members of multiple organisations.

- [**Project**](/flagsmith-concepts/data-model#projects): Projects contain one or more Environments that share a single set of Features across all of the Environments within the Project. Organisations can have any number of Projects.

- [**Role-Based Access Control (RBAC)**](/administration-and-security/access-control/rbac): A system for managing user permissions and access within an organisation.

- [**SDK (Software Development Kit)**](/integrating-with-flagsmith/integration-overview): Client libraries provided by Flagsmith for integrating feature flagging into applications.

- [**Segment**](/flagsmith-concepts/data-model#segments): A group of identities defined by traits (e.g., logins, device, location, or custom traits). You can override feature defaults for segments, such as enabling features for a "power user" group.

- [**Staged Rollout**](/managing-flags/rollout/rollout-by-percentage): Gradually enabling a feature for increasing percentages of your identities to reduce risk.

- [**Trait**](/flagsmith-concepts/data-model#traits): A key-value pair associated with an identity that can store any type of data.
