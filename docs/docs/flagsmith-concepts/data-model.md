---
title: Data Model
sidebar_label: Data Model
sidebar_position: 10
---

Flagsmith uses a flexible data model to help you manage feature flags and remote configurations across multiple projects, environments, and user groups.

Here's a high-level overview of the Flagsmith data model. Fear not - it's not as complex as it looks!

![Flagsmith Data Model](/img/flagsmith-model.svg)

OK let's break this down.

### Organizations
Organizations allow you and other team members to manage projects and their features. A user can be a member of multiple organizations.

### Projects
Projects contain one or more Environments that share a single set of Features. Organisations can have any number of Projects.

### Environments
Environments are a way to separate the configuration of your features. For example, a feature might be enabled in your project's Development and Staging environments but turned off in your Production environment. A project can have any number of environments.

### Features
Features are shared across all Environments within a Project, but their values/states can be modified per Environment. Features can be toggled on/off or assigned values (e.g., string, integer, boolean, or multivariate values).

### Identities
Identities are a particular user registration for one of your Project's Environments. Registering identities within the client application allows you to manage features for individual users. Identity features can be overridden from your environment defaults. For example, joe@yourwebsite.com would be a different identity in your development environment to the one in production, and they can have different features enabled for each environment.

For more info see [Identities](/basic-features/managing-identities).

### Traits
You can store any number of Traits against an Identity. Traits are key:value pairs that can store any type of data. Some examples of traits that you might store against an Identity might be:
- The number of times the user has logged in.
- If they have accepted the application terms and conditions.
- Their preferred application theme.
- If they have performed certain actions within your application.

For more info see [Traits](/basic-features/managing-identities.md#identity-traits).

### Segments
Segments define a group of users by traits such as login count, device, location or any number of custom defined traits. Similar to individual users, you can override environment defaults for features for a segment. For example, you might show certain features for a "power user" segment.

For more info see [Segments](/basic-features/segments.md).

## Relationships Summary

- **Organizations** contain **Projects**
- **Projects** contain **Environments** and **Features**
- **Environments** have their own configuration for each **Feature**
- **Identities** belong to an **Environment** and can be related to  **Traits**
- **Segments** group **Identities** by rules on **Traits**
