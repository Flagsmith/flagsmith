---
title: Flags API Reference
sidebar_label: Flags API
---

The Flags API is the public-facing API that your SDKs use to retrieve feature flags and remote configuration for your users. It's designed for high performance and low latency, with a globally distributed infrastructure to serve requests quickly, wherever your users are.

This API is used for **reading** flag states and user traits, not for managing your projects.

## Endpoints

The two main endpoints you will interact with via the SDKs are:

-   `/flags/`: Get all flags for a given environment.
-   `/identities/`: Get all flags and traits for a specific user identity.

For SaaS customers, the base URL for the Flags API is `https://edge.api.flagsmith.com/`. Our Edge API specification is detailed [here](/edge-api/overview). 