---
title: GitHub Integration
description: View your Flagsmith flags inside GitHub
sidebar_label: GitHub
hide_title: true
---

<img src="/img/integrations/github/github-logo.svg" alt="GitHub Logo" width="30%" />

View your Flagsmith Flags inside GitHub Issues and Pull Requests.

![Github Integration](/img/integrations/github/github-integration-1.png)

## Integration Setup (SaaS)

You can either set up the integration from the Flagsmith side or from the Github side.

### From Flagsmith

1. In the Integrations Option in the top navigation bar, find the GitHub integration and click on 'Add Integration'.
2. A window will open asking you to select the organization you belong to.
3. Select the repositories and save.
4. Back in the Flagsmith application, click on the 'Manage Integration' button.
5. Finally, select the repository you wish to link.

### From GitHub

1. In GitHub, add the app from the [GitHub Marketplace](https://github.com/apps/flagsmith).
2. Select your organisation.
3. Select your repositories where you want install the app.
4. You will be redirected back to the Flagsmith app to finish the integration setup.
5. Select your Flagsmith Organisation.
6. Select the Flagsmith Project you want to associate with the repository where the app was installed to create the
   Integration.

## Integration Setup (Self-Hosted)

### Creating and Configuring your GitHub App

You can create your own GitHub App by following these
[steps from GitHub Docs](https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/registering-a-github-app).

In the Permissions and Events section, configure the following permissions and events:

**Repository permissions**

- **Issues:** Read and write.
- **Metadata:** Read only (Mandatory)
- **Pull requests:** Read and write.

**Subscribe to events**

- **Pull Request**
- **Issues**

In the Post Installation section, you need to add the Setup URL and check the option 'Redirect on update':

**The setup URL:** This is the base URL of your Flagsmith dashboard, followed by `login?github-redirect=true`.

E.g. `https://flagsmith.example.com/login?github-redirect=true`

In the Webhook section, you need to check the 'active' option and add the webhook URL:

**The webhook URL:** This is the base URL of your Flagsmith API, followed by `github-webhook/`.

E.g. `https://flagsmith-api.example.com/api/v1/github-webhook/`

### Configuring Flagsmith

You must set the [API Env variables](/deployment/hosting/locally-api.md#github-integration-environment-variables) and
the [Frontend Env variables](/deployment/hosting/locally-frontend.md#github-integration-environment-variables) to use
your own GitHub App.

In the 'Webhook' section:

**Webhook secret:** Generate a random string of text with high entropy and put it in the field

## Adding a Flagsmith Flag to a GitHub issue or pull request

1. Create or select a Feature Flag.
2. Go to the 'Link' Tab inside the Feature modal.
3. Select your GitHub integration.
4. Select GitHub Issue or GitHub PR and Save.

## Removing the GitHub Integration

1. From Flagsmith, click 'Integrations', find the GitHub integration and click on 'Manage Integration'.
2. Click on 'Delete Integration' button, and confirm. 