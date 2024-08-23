---
title: Grafana Integration
description: Integrate Flagsmith with Grafana
sidebar_label: Grafana
hide_title: true
---

import ReactPlayer from 'react-player'

![Image](/img/integrations/grafana/grafana-logo.svg)

You can integrate Flagsmith with Grafana. Send flag change events from Flagsmith into Grafana as annotations.

The video below will walk you through the steps of adding the integration:

<ReactPlayer
    controls
    width="100%"
    height="460px"
    url='https://flagsmith.wistia.com/medias/z9vkon54qh' />

## Integration Setup

Log into Grafana and generate a Service Account Key:

1. Navigate to Administration > Users and access > Service accounts
2. Add Service Account
3. Change the Role selection to "Annotation Writer" or "Editor".
4. Click on Add service account token and make a note of the generated token.

In Flagsmith:

1. Navigate to Integrations, then add the Grafana integration.
2. Enter the URL for your web interface of your Grafana installation. For example, `https://grafana.flagsmith.com`.
3. Paste the service account token you created in Grafana to `Service account token` field.
4. Click Save.

Flag change events will now be sent to Grafana as _Organisation Level_
[Annotations](https://grafana.com/docs/grafana/latest/dashboards/build-dashboards/annotate-visualizations/).

You can view the annotations in your Grafana dashboards but going to Dashboard Settings > Annotations, selecting the
`Grafana` data source and then filtering on annotations that are tagged with the `flagsmith` tag.

Annotations reporting feature-specific events include the project tag and Flagsmith user-defined tags, and flag change
events include the environment tag as well.
