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

![GitLab integration overview](/img/integrations/gitlab/intro-screenshot.png)

## Setup

The integration supports
[personal access tokens](https://docs.gitlab.com/user/profile/personal_access_tokens/),
[group access tokens](https://docs.gitlab.com/user/group/settings/group_access_tokens/),
and [project access tokens](https://docs.gitlab.com/user/project/settings/project_access_tokens/).
All require the `api` scope. The token type determines which projects are
accessible in Flagsmith.

1. **In GitLab**
   1. Create an access token with the `api` scope.
   1. Copy the token — you will not see it again.
1. **In Flagsmith**
   1. Go to Integrations > **GitLab** > Add Integration.
   1. Set the **GitLab Instance URL** to your instance
      (e.g. `https://gitlab.example.com` or `https://gitlab.com`).
   1. Paste the access token.
   1. Click "Save". ✅

![GitLab integration configuration](/img/integrations/gitlab/add-configuration.png)

:::tip

Remember to rotate your GitLab access token before it expires.

:::

## Linking issues and merge requests to feature flags

1. Open a feature flag and go to the **Links** tab.
1. Select a GitLab project.
1. Choose **Issue** or **Merge Request**.
1. Search and select the item you want to link.

![Selecting a GitLab issue to link](/img/integrations/gitlab/select-issue-for-linking.png)

Flagsmith will post a comment to the linked issue or MR with the flag's current
state across all environments. When the flag state changes, a new comment is
posted automatically.

A **Flagsmith Feature** label is added to linked issues and merge requests so your
team can filter for them in GitLab.

## Automatic state sync

When a linked issue or merge request changes state in GitLab — closed, merged,
or reopened — Flagsmith automatically updates the linked feature flag's tags to
reflect the current state. This is powered by webhooks that Flagsmith registers
on your GitLab projects automatically.

## Removing the integration

Go to Integrations > GitLab > Manage Integration > Delete Integration.
