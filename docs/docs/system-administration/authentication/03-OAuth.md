---
title: OAuth
---

### Google

To configure OAuth for Google:

- [Setting up OAuth 2.0](https://support.google.com/cloud/answer/6158849?hl=en)
- Create the Flagsmith on Flagsmith flag as it shows [here](/deployment/overview#oauth_google).

### GitHub

As a pre-requisite for this configuration make sure to have
[Flagsmith on Flagsmith](/deployment/overview#running-flagsmith-on-flagsmith) set up.

Configure the following environment variables:

- `GITHUB_CLIENT_ID`
- `GITHUB_CLIENT_SECRET`

To configure OAuth for GitHub:

- [Create an OAuth GitHub application](https://docs.github.com/en/developers/apps/building-oauth-apps/creating-an-oauth-app)
- For the Authorization callback URL use: `https://<your flagsmith domain name>/oauth/github`
- Create the Flagsmith on Flagsmith flag as it shows [here](/deployment/overview#oauth_github).

Now you would be able to see the GitHub SSO option.

<div style={{textAlign: 'center'}}><img width="75%" src="/img/Flagsmith_GitHub_SignUp.png"/></div>
