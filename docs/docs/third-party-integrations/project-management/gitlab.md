---
title: GitLab Integration
description: Link GitLab issues and merge requests to Flagsmith feature flags
sidebar_label: GitLab
hide_title: true
---

<img src="/img/integrations/gitlab/gitlab-logo.svg" alt="GitLab Logo" width="30%" />

Link GitLab issues and merge requests to your Flagsmith feature flags. When a
flag changes state, Flagsmith posts a comment to the linked issue or MR showing
the flag's current state across all environments.

Flagsmith offers two integration cards depending on your GitLab setup:

- **GitLab** — for teams using GitLab.com. One-click OAuth.
- **GitLab Self-Hosted** — for teams running their own GitLab instance. Uses a
  personal access token.

Both integrations share the same features once connected.

## Setup: GitLab.com

1. In Flagsmith, go to Integrations > **GitLab** > Add Integration.
1. Click "Authorise". You will be sent to GitLab to grant Flagsmith access.
1. Once back in Flagsmith, the integration is active. ✅

:::note

Flagsmith requests the `api`
[scope](https://docs.gitlab.com/integration/oauth_provider/), which grants
read and write access to the GitLab API. This is required to post comments and
manage labels on your issues and merge requests.

:::

## Setup: Self-hosted GitLab

1. **In GitLab**
   1. Open your
      [Access Tokens settings](https://docs.gitlab.com/user/profile/personal_access_tokens/).
   1. Create a new token with the `api` scope.
   1. Copy the token — you will not see it again.
1. **In Flagsmith**
   1. Go to Integrations > **GitLab Self-Hosted** > Add Integration.
   1. Set the **GitLab Instance URL** to your instance
      (e.g. `https://gitlab.example.com`).
   1. Paste the access token.
   1. Click "Save". ✅

:::tip

Personal access tokens on GitLab
[expire after at most 365 days](https://docs.gitlab.com/user/profile/personal_access_tokens/)
(400 days on GitLab 17.6+). Remember to rotate your token before it expires.

:::

## Linking issues and merge requests to feature flags

1. Open a feature flag and go to the **Link** tab.
1. Select a GitLab project.
1. Choose **Issue** or **Merge Request**.
1. Search and select the item you want to link.

Flagsmith will post a comment to the linked issue or MR with the flag's current
state across all environments. When the flag state changes, a new comment is
posted automatically.

A **Flagsmith Flag** label is added to linked issues and merge requests so your
team can filter for them in GitLab.

## Automatic state sync

When a linked issue or merge request changes state in GitLab — closed, merged,
or reopened — Flagsmith automatically updates the linked feature flag's tags to
reflect the current state. This is powered by webhooks that Flagsmith registers
on your GitLab projects automatically.

## Removing the integration

Go to Integrations > GitLab > Manage Integration > Delete Integration.
