---
title: GitHub
description: View your Flagsmith flags inside GitHub
sidebar_position: 10
hide_title: true
---

<img src="/img/integrations/github/github-logo.svg" alt="GitHub Logo" width="30%" height="30%"/>

View your Flagsmith Flags inside GitHub Issues and Pull Requests.

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

## Adding a Flagsmith Flag to a GitHub issue or pull request

1. Create or select a Feature Flag.
2. Go to the 'Link' Tab inside the Feature modal.
3. Select your GitHub integration.
4. Select GitHub Issue or GitHub PR and Save.

## Removing the GitHub Integration

1. From Flagsmith, click 'Integrations', find the GitHub integration and click on 'Manage Integration'.
2. Click on 'Delete Integration' button, and confirm.

## Integration Setup (Self-Hosted)

You have to set the [API Env variables](/deployment/hosting/locally-api.md#github-integration-environment-variables) and
the [Frontend Env variables](/deployment/hosting/locally-frontend.md#github-integration-environment-variables) for your
GitHub to use your own GitHub App.
