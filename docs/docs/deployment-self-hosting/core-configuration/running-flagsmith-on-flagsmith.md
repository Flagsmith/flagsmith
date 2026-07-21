---
title: 'Running Flagsmith on Flagsmith'
description: 'How to configure a self-hosted instance to use its own flags for feature management.'
sidebar_position: 50
---

Flagsmith uses Flagsmith to control features on the frontend dashboard. If you are self-hosting the platform, you will
sometimes see features greyed out, or you may want to disable specific features, e.g. logging in via Google and GitHub.
If you are using your own Flagsmith environment, then you will need to have a replica of our flags in order to control
access to those features.

## Setup Process

To do this, first create a new project within your self-hosted Flagsmith application. This is the project that we will
use to control the features of the self-hosted Flagsmith instance. We will then point the self-hosted frontend dashboard
at this Flagsmith project in order to control what features show for your self-hosted Flagsmith instance.

## Environment Variables

Once you have created the project, you need to set the following
[Frontend](https://github.com/Flagsmith/flagsmith-frontend) environment variables in order to configure this:

- `FLAGSMITH_ON_FLAGSMITH_API_KEY`
  - The Flagsmith Client-side Environment Key we use to manage features - Flagsmith runs on Flagsmith. This will be the
    API key for the project you created as instructed above.
- `ENABLE_FLAGSMITH_REALTIME`
  - Determines whether the Flagsmith on Flagsmith SDK uses Realtime.
- `FLAGSMITH_ON_FLAGSMITH_API_URL`
  - The API URL which the Flagsmith frontend dashboard should communicate with. This will most likely be the domain name
    of the Flagsmith API you are self-hosting: Flagsmith runs on Flagsmith. E.g. For our SaaS hosted platform, the
    variable is `https://edge.api.flagsmith.com/api/v1/`. For example, if you were running everything locally using the
    standard [docker-compose setup](https://github.com/Flagsmith/flagsmith-docker), you would use
    `http://localhost:8000/api/v1/`

## Verification and Usage

Once you have set this up, you should see the Flagsmith frontend requesting its own flags from the API (you can look in
your browser developer console to see this). You can now start creating flags and overriding the default behaviours of
the platform. See the [flag reference below](#current-feature-flags) for the full list of available flags.

## Current Feature Flags

:::info Default Behaviour

The self-hosted Flagsmith frontend ships with sensible defaults for most flags via a built-in
[default configuration](https://github.com/Flagsmith/flagsmith/blob/main/frontend/common/stores/default-flags.ts). You
only need to create flags in your Flagsmith on Flagsmith project if you want to **override** these defaults — for
example, to enable OAuth login or disable certain UI features.

:::

### Authentication & SSO

| Flag Name                    | Value  | Description                                                                              |
| ---------------------------- | ------ | ---------------------------------------------------------------------------------------- |
| `oauth_github`               | JSON   | Enables GitHub OAuth login. [See below.](#oauth_github)                                  |
| `oauth_google`               | JSON   | Enables Google OAuth login. [See below.](#oauth_google)                                  |
| `saml`                       | —      | Enables SAML authentication options in the login UI.                                     |
| `sso_idp`                    | String | When set, auto-redirects to a pre-configured SAML IdP instead of showing the login form. |
| `disable_oauth_registration` | —      | Hides OAuth buttons on the signup page (existing users can still log in via OAuth).      |

### Organisation Management

| Flag Name            | Value | Description                                            |
| -------------------- | ----- | ------------------------------------------------------ |
| `disable_create_org` | —     | Prevents users from creating additional organisations. |

### UI & Messaging

| Flag Name      | Value  | Description                                                          |
| -------------- | ------ | -------------------------------------------------------------------- |
| `announcement` | JSON   | Shows a dismissible announcement banner. [See below.](#announcement) |
| `butter_bar`   | String | Shows a message bar at the top of all pages (supports HTML).         |

### Integrations & Configuration

| Flag Name           | Value | Description                                                                                                                                                                                                                                                                  |
| ------------------- | ----- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `integration_data`  | JSON  | Defines available third-party integrations and their configuration fields. The frontend includes a [comprehensive default](https://github.com/Flagsmith/flagsmith/blob/main/frontend/common/stores/default-flags.ts) — only override to customise which integrations appear. |
| `segment_operators` | JSON  | Defines available segment rule operators. The frontend includes a [comprehensive default](https://github.com/Flagsmith/flagsmith/blob/main/frontend/common/stores/default-flags.ts) — override to remove operators you don't need from the segment rules UI.                 |

### `oauth_github`

Find instructions for GitHub Authentication [here](/administration-and-security/access-control/oauth#github).

Create an OAuth application in the GitHub Developer Console and then provide the following as the flag value, replacing
your `client_id` and `redirect_uri`:

```json
{
 "url": "https://github.com/login/oauth/authorize?scope=user&client_id=<your client_id>&redirect_uri=<your url-encoded redirect uri>"
}
```

### `oauth_google`

Create an OAuth application in the Google Developer Console and then provide the following as the flag value:

```json
{
 "clientId": "<Your Google OAuth Client ID>"
}
```

If you are using the [unified Docker image](https://hub.docker.com/repository/docker/flagsmith/flagsmith), which serves
both the API and the frontend through Django, ensure you configure the following environment variable in your
deployment:

```
DJANGO_SECURE_CROSS_ORIGIN_OPENER_POLICY=same-origin-allow-popups
```

For those hosting the frontend independently, make sure you set the `Cross-Origin-Opener-Policy` header to
`same-origin-allow-popups` for the Google OAuth flow to work.

### `announcement`

The `announcement` flag value is a JSON object with the following shape:

```json
{
 "id": "unique-id",
 "title": "Announcement Title",
 "description": "A short description shown in the banner.",
 "buttonText": "Learn More",
 "url": "https://example.com",
 "isClosable": true
}
```
