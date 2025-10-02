---
title: Data Model
sidebar_label: Data Model
sidebar_position: 1
---

Flagsmith uses a flexible data model to help you manage feature flags and remote configurations across multiple projects, environments, and user groups.

Here's a high-level overview of the Flagsmith data model. 

![Image](/img/flagsmith-model.svg)

## Key Concepts

Below you'll find a quick explanation of the main building blocks that make up the Flagsmith data model.

### Organisations

Organisations allow you and other team members to manage projects and their features. A user can be a member of multiple organisations.

### Projects

Projects contain one or more environments that share a single set of features. Organisations can have any number of projects. Paid/paying organisations can have unlimited number of projects.

### Environments

Environments are a way to separate the configuration of your features. For example, a feature might be enabled in your project's Development and Staging environments but turned off in your Production environment. A project can have any number of environments.

### Features

Features are shared across all environments within a project, but their values/states can be modified per environment. Features can be toggled on/off or assigned values (e.g., string, integer, boolean, or multivariate values).

### Identities

Identities are individual users associated with each environment. Registering identities within the client application allows you to manage features for individual users. Identity features can be overridden from your environment defaults. For example, joe@yourwebsite.com would be a different identity in your development environment to the one in production, and they can have different features enabled for each environment.

For more information, see [Identities](/flagsmith-concepts/identities).

### Traits

You can store any number of traits against an identity. Traits are key-value pairs that can store any type of data. Some examples of traits that you might store against an identity include:

- The number of times the user has logged in.
- Whether they have accepted the application terms and conditions.
- Their theme preference (eg. dark mode).
- Whether they have performed certain actions within your application.

For more information, see [Traits](/flagsmith-concepts/identities#identity-traits).

### Segments

Segments define a group of users by traits such as login count, device, location, or any number of custom-defined traits. Similar to individual users, you can override environment defaults for features for a segment. For example, you might show certain features for a "power user" segment.

For more information, see [Segments](/flagsmith-concepts/segments).
