---
title: Discord Integration
description: Post Flagsmith flag and segment changes to a Discord channel
sidebar_label: Discord
---

You can integrate Flagsmith with Discord. Flagsmith posts a message to a Discord channel whenever a feature, flag state
or segment in your project changes, so your team sees changes where it already talks.

The integration uses a Discord channel webhook. You don't need to install a bot or grant any OAuth permissions, and it
works the same on Flagsmith Cloud and on self-hosted Flagsmith.

## Integration setup

1. In Discord, open the channel you want to post to, then go to **Edit Channel > Integrations > Webhooks > New
   Webhook**. Name it (for example, "Flagsmith") and click **Copy Webhook URL**.
2. In Flagsmith, go to your project and click **Integrations**. Then click **Add Integration** next to Discord.
3. Paste the webhook URL and click **Save**.

The webhook URL contains a secret token. Anyone who has it can post to the channel, so treat it like a password. If it
leaks, delete the webhook in Discord and create a new one.

Flagsmith only accepts Discord webhook URLs, in the form `https://discord.com/api/webhooks/<id>/<token>`.

## What gets posted

Each change is posted as an embed with:

- the audit log message, for example `Flag state / Remote config value updated for feature: dark_mode`
- the project and, where there is one, the environment
- who made the change
- when the change was made

Messages never mention anyone, even if a feature or segment name contains `@everyone` or `@here`.

Flagsmith posts feature, flag state and segment changes. Other audit log events, such as environment settings changes,
are not posted.

## Self-hosted Flagsmith

Your Flagsmith API must be able to make outbound HTTPS requests to `discord.com`. Messages are sent by the task
processor when it is enabled, or by the API otherwise.
