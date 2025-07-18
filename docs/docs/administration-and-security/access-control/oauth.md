---
title: OAuth
sidebar_label: OAuth
sidebar_position: 40
---

This guide explains how to set up OAuth authentication for Flagsmith using Google and GitHub as identity providers. OAuth allows your users to log in to Flagsmith using their existing credentials from these services.

## Prerequisites

- Administrative access to your Flagsmith instance to configure environment variables and Flagsmith on Flagsmith flags.
- An account with Google Cloud Console and/or GitHub with permissions to create OAuth applications.
 
## Configure OAuth for Google

Follow these steps to set up OAuth with Google:

1. Follow Google's official guide on [Setting up OAuth 2.0](https://support.google.com/cloud/answer/6158849?hl=en) to create your OAuth 2.0 client ID and client secret.
- Create the Flagsmith on Flagsmith flag as detailed in the [deployment documentation](/deployment#oauth_google).

## Configure OAuth for GitHub

As a pre-requisite for this configuration make sure to have [Flagsmith on Flagsmith](/deployment#running-flagsmith-on-flagsmith) set up. Follow these steps to set up OAuth with GitHub:

1. Configure the following environment variables:
    - `GITHUB_CLIENT_ID`
    - `GITHUB_CLIENT_SECRET`

2. Configure OAuth for GitHub:
    - [Create an OAuth GitHub application](https://docs.github.com/en/developers/apps/building-oauth-apps/creating-an-oauth-app)
    - For the Authorization callback URL use: `https://<your flagsmith domain name>/oauth/github`
3. Create the Flagsmith on Flagsmith flag as it shows [here](/deployment#oauth_github).

Now you would be able to see the GitHub SSO option.

<div style={{textAlign: 'center'}}><img width="75%" src="/img/Flagsmith_GitHub_SignUp.png"/></div>

## See Also

- [Flagsmith Deployment Documentation](/deployment#running-flagsmith-on-flagsmith): For detailed information on setting up "Flagsmith on Flagsmith" and related configurations.
- [SAML SSO](/administration-and-security/access-control/saml): For information on configuring SAML-based SSO.