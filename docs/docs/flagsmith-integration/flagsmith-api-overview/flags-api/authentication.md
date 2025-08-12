---
title: Authentication
sidebar_label: Authentication
---

The Flags API uses a non-secret **Environment Key** for authentication. This key is safe to be exposed in public, client-side applications.

## Finding Your Environment Key

You can find the Environment Key for each of your environments in the Flagsmith dashboard.

1.  Navigate to the Project you want to work with.
2.  Go to the **Environments** tab.
3.  You will see a list of your environments, each with its own Client-side Environment Key.

## Using the Environment Key

You must supply the Environment Key with each request in an HTTP header named `X-Environment-Key`.

```bash
X-Environment-Key: <Your client-side SDK key>
```

The SDKs handle this for you automatically when you initialize them with the key. If you are making direct calls to the API, you will need to include this header in every request. 