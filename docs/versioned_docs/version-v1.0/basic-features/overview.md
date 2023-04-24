---
title: Feature Flags - An Overview
sidebar_label: Overview
sidebar_position: 1
---

Feature Flags are a development methodology that allow you to ship code and features before they are finished. This
greatly benefits Continuous Integration and Continuous Deployment (CI/CD). The typical workflow for this is as follows.

1. You are about to start work on a new feature. Lets imaging you are going to implement a sharing button with your
   application.
2. Create a new Feature Flag in Flagsmith, calling it "sharing_button". Set it to enabled on your development
   environment, and disabled on your production environment.
3. Start working on the feature. Whenever you write code that shows the button within the UI, wrap it in a conditional
   statement, testing against the value of the flag "sharing button". Only show the button if the flag is set to True.
4. Because your button only shows when the "sharing_button" flag is set to True, you are safe to commit your code as you
   work on the feature. Your code will be live within the production platform, but the functionality is hidden behind
   the flag.
5. Once you are happy with your Feature, you can enable the "sharing_button" for other members of your team and with
   Beta testers.
6. If everything is working as intended, simply flip the "sharing_button" flag to True for everyone in your production
   environment, and your feature is rolled out.

If you want to learn more about Feature Flags,
[Flickr wrote the seminal blog post on it in 2009](https://code.flickr.net/2009/12/02/flipping-out/)

## Flagsmith Model

Here's a high level overview of the data model for Flagsmith. Fear not - it's not as complex as it looks!

![Image](/img/flagsmith-model.svg)

OK let's break this down.

### Organisations

Organisations are a way for you and other team members to manage projects and their features. Users can be members of
multiple organisations.

### Projects

Projects contain one or more Environments that share a single set of Features across all of the Environments within the
Project. Organisations can have any number of Projects.

### Environments

Environments are a way to separate the configuration of your features. For example, your project's Development and
Staging environments might have a feature configured as on while it is turned off in your Production environment. A
project can have any number of environments.

### Features

Features are shared between all the Environments within the Project, but their values/states can be modified between
Environments.

### Identities

Identities are a particular user registration for one of your Project's environments. Registering identities within the
client application allows you to manage features for individual users. Identity features can be overridden from your
environment defaults. For example, joe@yourwebsite.com would be a different identity in your development environment to
the one in production, and they can have different features enabled for each environment.

For more info see [Identities](/basic-features/managing-identities).

### Traits

You can store any number of Traits against an Identity. Traits are simple name:value pairs that can store any type of
data. Some examples of traits that you might store against an Identity might be:

- The number of times the user has logged in.
- If they have accepted the application terms and conditions.
- Their preference for application theme.
- If they have performed certain actions within your application.

For more info see [Traits](/basic-features/managing-identities.md#identity-traits).

### Segments

Segments are a way to define a group of users by traits such as number of times logged in, device, location or any
number of custom defined traits.

Similarly to individual users, you will be able to override environment defaults for features. For example showing
certain features for a "power user" segment.

For more info see [Segments](/basic-features/managing-segments.md).
