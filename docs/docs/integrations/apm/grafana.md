---
title: Grafana Integration
description: Integrate Flagsmith with Grafana
sidebar_label: Grafana
hide_title: true
---

![Image](/img/integrations/grafana/grafana-logo.svg)

You can integrate Flagsmith with Grafana. Send flag change events from Flagsmith into Grafana as annotations.

## Integration Setup

Log into Grafana and generate a Service Account Key:

1. Navigate to Administration > Users and access > Service accounts
2. Add Service Account
3. Change the Role selection to "Annotation Writer" or "Editor".
4. Click on Add service account token and make a note of the generated token.

In Flagsmith:

1. Navigate to Integrations, then add the Grafana integration
2. Enter the URL for your web interface of your Grafana installation. For example, `https://grafana.flagsmith.com/`.
   Make sure to add the trailing slash.
3. The `API Key` is the service account token you created in Grafana.
4. Click Save.

Flag change events will now be sent to Grafana as _Organisation Level_
[Annotations](https://grafana.com/docs/grafana/latest/dashboards/build-dashboards/annotate-visualizations/).

You can view the annotations in your Grafana dashboards but going to Dashboard Settings > Annotations, selecting the
`Grafana` data source and then filtering on annotations that are tagged with the `Flagsmith Event` tag.
