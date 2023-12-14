---
title: Jira
description: View your Flagsmith flags inside Jira
sidebar_position: 10
---

View your Flagsmith flags inside Jira.

:::tip

- The Jira integration is currently only supported with our hosted Flagsmith SaaS service. We are working on making it
  possible for those self hosting Flagsmith to use their own Jira app. Stay tuned!

:::

## Integration Setup

1. You need to provide your Flagsmith API key to Jira. You can get your API key by going to `Account > Keys` in
   Flagsmith.
2. In Jira, add the app from the
   [Atlassian Marketplace](https://marketplace.atlassian.com/apps/1232743/flagsmith-for-jira).
3. When prompted, add the Flagsmith API key.
4. If you are a member of more than one Organisation, select the Organisation you want to associate with the
   Integration. Otherwise you can skip this step.
5. Go back to the Jira project, click `Project Settings > Connect Flagsmith project` and select the Flagsmith Project
   you want to associate. Click Save.

## Adding a Flagsmith Flag to a Jira ticket

Open a ticket and click the Flagsmith button:

![Jira Flagsmith button](/img/integrations/jira/select-flagsmith.png)

---

Select the Flag you want to associate with the Jira ticket:

![Jira associate Flag](/img/integrations/jira/associate-flag.png)

---

Flag states now show inside Jira:

![Jira Flagsmith flag states](/img/integrations/jira/flag-states.png)

---

## Additional Tips

- You can associate multiple flags to a single Jira ticket.
