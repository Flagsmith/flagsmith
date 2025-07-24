---
title: Integration Overview
sidebar_label: Integration Overview
sidebar_position: 10
---

Flagsmith is designed to be integrated into your applications in a variety of ways, depending on your architecture and requirements. This guide provides an overview of the different integration options available.

## Deciding between Front-end and Back-end Flags

One of the first decisions to make when integrating Flagsmith is whether to evaluate flags on the front-end (client-side) or back-end (server-side).

### Front-end / Client-side

Client-side SDKs (for browsers, mobile apps, etc.) are great for features that directly impact the user interface, such as showing or hiding a new element, changing button colours, or running A/B tests on UI components.

- **Pros:** Fast UI updates, easy to implement for UI-related features.
- **Cons:** The Environment Key is public, and segment/targeting rules are not exposed to the client to prevent leaking sensitive information.

### Back-end / Server-side

Server-side SDKs run in your trusted back-end environment. They are ideal for controlling deeper application logic, such as enabling a new API endpoint, changing the behaviour of an algorithm, or managing access to certain features based on user permissions that are only known on the server.

- **Pros:** Secure environment, full access to all targeting rules, can be used to control critical application logic.
- **Cons:** May require an additional API call from the front-end to the back-end to get the flag state if it's needed in the UI.

You can read more about the differences in our [SDKs Overview documentation](../clients).

## Identities and Traits

To get the most out of Flagsmith, you'll want to identify your users. This allows you to:

-   Override flags for specific users.
-   Run A/B tests.
-   Gradually roll out features to a percentage of your users.
-   Target features to specific segments of users.

An **Identity** represents a single user in your application. You can also store **Traits** against an identity. Traits are key-value pairs that describe a user, for example, their subscription plan, their location, or how many times they've logged in.

You can learn more in our documentation on [Managing Identities](../basic-features/managing-identities.md).

### Transient Traits and Identities

For privacy-sensitive use cases, you can use transient traits and identities. This allows you to evaluate flags based on user data without persisting that data in Flagsmith. This is useful for things like:

-   Using PII (Personally Identifiable Information) for segmentation without storing it.
-   Running experiments on anonymous users.
-   Temporarily overriding a trait for a single session.

Learn more about this feature in our [Transient Traits and Identities documentation](../advanced-use/transient-traits.md).

## Third-party Integrations

Flagsmith also integrates with a variety of third-party tools for analytics, project management, and more. You can browse all available integrations in the [Integrations section](../integrations). 