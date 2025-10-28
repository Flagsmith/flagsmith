---
title: Code Examples
sidebar_label: Code Examples
---

Here are some `curl` examples demonstrating how to interact directly with the Flags API.

### Get Environment Flags

This command retrieves all the default flag states and remote config values for a specific environment.

```bash
curl 'https://edge.api.flagsmith.com/api/v1/flags/' \
    -H 'X-Environment-Key: <Your client-side SDK key>'
```

### Get Flags for an Identified User

This command performs the entire SDK identity workflow in a single call:

1.  Lazily creates an identity if it doesn't already exist.
2.  Sets or updates traits for that identity.
3.  Receives the flags for that identity, including any segment or identity-specific overrides.

```bash
curl --request POST 'https://edge.api.flagsmith.com/api/v1/identities/' \
    --header 'X-Environment-Key: <Your client-side SDK key>' \
    --header 'Content-Type: application/json' \
    --data-raw '{
        "identifier":"user_12345",
        "traits": [
            {
                "trait_key": "subscription_plan",
                "trait_value": "premium"
            },
            {
                "trait_key": "has_beta_access",
                "trait_value": true
            }
        ]
    }'
``` 