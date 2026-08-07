---
title: Authentication
sidebar_label: Authentication
---

To interact with the Admin API, you need to authenticate your requests using an API Token associated with your
Organisation, or a short-lived access token obtained through an [OIDC trust relationship](#oidc-trust-relationships).

## Generating an API Token

You can generate an API Token from the **Organisation Settings** page in the Flagsmith dashboard.

1. Click on your Organisation name in the top navigation panel.
2. Go to the **API Access** tab.
3. Click **Create API Key**.

Give your key a descriptive name so you can remember what it's used for.

## Using the API Token

Once you have your token, you need to include it in your API requests as an `Authorization` header. The token should be
prefixed with `Api-Key`.

```bash
Authorization: Api-Key <API TOKEN FROM ORGANISATION PAGE>
```

This token grants access to manage all projects within that organisation, so be sure to keep it secure and never expose
it in client-side applications.

For SaaS customers, the base URL for the Admin API is `https://api.flagsmith.com/`. If you are self-hosting, you will
need to use your own API URL.

## OIDC trust relationships

Trust relationships let a workload that already has an OIDC identity — for example, a GitHub Actions job — call the
Admin API without any stored secrets. The workload exchanges its OIDC token for a short-lived Flagsmith access token, in
the same way cloud providers implement workload identity federation.

### Configuring a trust relationship

1. Click on your Organisation name in the top navigation panel.
2. Go to the **API Access** tab.
3. Under **Trust relationships**, click **Add trust relationship** and pick a provider.

#### GitHub Actions

The GitHub Actions form only asks for a repository and, optionally, a GitHub environment:

- **Repository**: with the Flagsmith GitHub integration installed, pick the repository from a list — the trust
  relationship then pins the repository's immutable ID, which is robust against renames. Without the integration, type
  the owner and name, which are matched against the token's `repository` claim.
- **GitHub environment**: if set, tokens must carry the matching `environment` claim, so the workflow job must run in
  that GitHub environment.
- **Is admin / roles**: the permissions granted to exchanged tokens — either full organisation admin, or a set of RBAC
  roles, exactly as with Master API Keys.

The form shows a ready-made workflow snippet reflecting your configuration.

#### Other OIDC providers

The freeform option supports any OIDC identity provider, such as GitLab CI or Kubernetes:

- **Trusted issuer URL**: the OIDC issuer. The issuer must serve OIDC discovery metadata over HTTPS.
- **Expected audience**: the `aud` claim the token must carry. Each issuer and audience pair must be unique, so use a
  distinct audience per trust relationship.
- **Claim matching rules**: additional claims the token must match. Values support `*` wildcards, and a rule matches if
  any of its values match. All rules must match.
- **Is admin / roles**: as above.

### Exchanging a token

`POST /api/v1/auth/oidc/token/` with the OIDC token in the request body:

```bash
curl -X POST 'https://api.flagsmith.com/api/v1/auth/oidc/token/' \
  -H 'Content-Type: application/json' \
  -d '{"token": "<OIDC TOKEN>"}'
```

A successful exchange returns a short-lived access token:

```json
{
 "access_token": "<ACCESS TOKEN>",
 "token_type": "Bearer",
 "expires_in": 3600
}
```

Use it as a bearer token on Admin API requests:

```bash
Authorization: Bearer <ACCESS TOKEN>
```

Access tokens expire after one hour by default. Deleting a trust relationship, or changing its roles, applies to
already-issued tokens immediately. Exchanged tokens cannot manage API keys or trust relationships.
