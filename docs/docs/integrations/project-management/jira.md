---
title: Jira
description: View your Flagsmith flags inside Jira
sidebar_position: 10
---

View your Flagsmith flags inside Jira.

:::tip

The Jira integration is currently in beta. Please contact us to join the beta!

:::

## Integration Setup

todo: Correct the link

1. Add the app from the
   [Atlassian Marketplace](https://developer.atlassian.com/console/install/3fd8c838-2ced-45a5-8807-0401ec45a096?signature=5f47a1c11336d3ecd75054fbd534d808e5b22dd98afe47ceacee5ea6918426bc19bb2c2f7e740f2fed79d1d96b5b1fd007a088a684e85681fada20617e227083&product=jira).
2. You need to provide your Flagsmith API key to Jira. You can get your API key by going to Account > Keys in Flagsmith.
3. Add the API key to Jira when prompted.
4. Select the Organisation you want to connect and click Save.
5. In the Jira project, click Project Settings > Connect Flagsmith project and select the Flagsmith Project you want to
   associate. Click Save.

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
