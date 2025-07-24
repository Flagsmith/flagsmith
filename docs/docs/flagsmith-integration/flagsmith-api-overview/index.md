---
title: Flagsmith API Overview
sidebar_label: Overview
---

The Flagsmith API is divided into two distinct parts, each serving a different purpose. Understanding the difference is key to integrating with Flagsmith effectively.

### 1. The Flags API (Public SDK API)

This is the API that your client and server-side SDKs interact with to get flag and remote configuration values for your environments and users. It's designed to be fast, scalable, and publicly accessible.

- **Purpose:** Serving flags to your applications.
- **Authentication:** Uses a public, non-secret **Environment Key**.
- **Security:** Open by design. The Environment Key can be exposed in client-side code.

[Learn more about the Flags API](./flags-api).

### 2. The Admin API (Private Admin API)

This is the API you use to programmatically manage your Flagsmith projects. Anything you can do in the Flagsmith dashboard, you can also do via the Admin API.

- **Purpose:** Creating, updating, and deleting projects, environments, flags, segments, and users.
- **Authentication:** Uses a secret **Organisation API Token**.
- **Security:** Requires a secret key that should never be exposed in client-side code.

[Learn more about the Admin API](./admin-api). 