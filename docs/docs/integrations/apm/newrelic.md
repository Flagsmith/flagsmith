---
title: New Relic Analytics Integration
description: Integrate Flagsmith with New Relic
sidebar_label: New Relic
hide_title: true
---

![Image](/img/integrations/newrelic/newrelic-logo.svg)

You can integrate Flagsmith with New Relic. Send flag change events from Flagsmith into your New Relic event stream.

## Integration Setup

1. Log into New Relic and navigate to the APM project that you want to integrate with. Make a note of the `App ID`.
2. Generate a New Relic API key. Account Settings > API keys > Create Key. The Key type is `User`.
3. Go to your Flagsmith project, and click Integrations. Add the New Relic Integration. Enter the New Relic `API Key`
   and `App ID`. For the API URL, enter either:
   - `https://api.newrelic.com/` for the US datacenter
   - `https://api.eu.newrelic.com/` for the EU datacenter
4. Click Save.

Flag change events will now be sent to New Relic as `Deployments`.
