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

## Setup

The integration requires a token with access to the full GitLab group —
either a [personal access token](https://docs.gitlab.com/user/profile/personal_access_tokens/)
or a [group access token](https://docs.gitlab.com/user/group/settings/group_access_tokens/).
Project access tokens are not supported yet.

1. **In GitLab**
   1. Create a personal access token or group access token with the `api` scope.
   1. Copy the token — you will not see it again.
1. **In Flagsmith**
   1. Go to Integrations > **GitLab** > Add Integration.
   1. Set the **GitLab Instance URL** to your instance
      (e.g. `https://gitlab.example.com` or `https://gitlab.com`).
   1. Enter your **GitLab Group** (e.g. `my-company`).
   1. Paste the access token.
   1. Click "Save". ✅

:::tip

Remember to rotate your GitLab access token before it expires.

:::

## Linking issues and merge requests to feature flags

1. Open a feature flag and go to the **Link** tab.
1. Select a GitLab project from your connected group.
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
