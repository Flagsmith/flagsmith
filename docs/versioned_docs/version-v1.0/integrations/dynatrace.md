---
title: Dynatrace Integration
sidebar_label: Dynatrace
hide_title: true
---

![Dynatrace](/img/integrations/dynatrace/dynatrace-logo.svg)

You can integrate Flagsmith with Dynatrace. Send flag change events from Flagsmith into your Dynatrace event stream.

## Integration Setup

1. Log into Dynatrace create a new Access Token with the following permissions:
   - `API v2 scopes` : `Ingest events`
2. Go to Flagsmith > Integrations > Dynatrace > Add Integration
3. Select the `Flagsmith Environment` you want to track.
4. The `Base URL` depends on your Dynatrace installation:
   - Managed: `https://{your-domain}/e/{your-environment-id}/`
   - SaaS: `https://{your-environment-id}.live.dynatrace.com/`
   - Environment ActiveGate: `https://{your-activegate-domain}/e/{your-environment-id}/`
5. The `API Key` is the Access Token you created in step 1.
6. The `Entity Selector` defines which Dynatrace entities you want to associate Flag Change events with.
   [Check the Dynatrace Docs](https://www.dynatrace.com/support/help/dynatrace-api/environment-api/entity-v2/entity-selector)
   for more information on those.

## How It Works

Once the setup is complete, try changing a Flag value in the Environment you configured during setup. Then look at one
of the Dynatrace Entities defined in the `Entity Selector`. You will see Deployment Events show up in the Events panel.

![Dynatrace Events](/img/integrations/dynatrace/dynatrace-events-panel.png)
