---
title: Authentication
sidebar_label: Authentication
---

To interact with the Admin API, you need to authenticate your requests using an API Token associated with your Organisation.

## Generating an API Token

You can generate an API Token from the **Organisation Settings** page in the Flagsmith dashboard.

1.  Click on your Organisation name in the top navigation panel.
2.  Go to the **API Keys** tab.
3.  Click **Create API Key**.

Give your key a descriptive name so you can remember what it's used for.

## Using the API Token

Once you have your token, you need to include it in your API requests as an `Authorization` header. The token should be prefixed with `Api-Key`.

```bash
Authorization: Api-Key <API TOKEN FROM ORGANISATION PAGE>
```

This token grants access to manage all projects within that organisation, so be sure to keep it secure and never expose it in client-side applications.

For SaaS customers, the base URL for the Admin API is `https://api.flagsmith.com/`. If you are self-hosting, you will need to use your own API URL. 