---
title: Grafana Integration
description: Integrate Flagsmith with Grafana
sidebar_label: Grafana
hide_title: true
---

import ReactPlayer from 'react-player'

![Image](/img/integrations/grafana/grafana-logo.svg)

Integrate Flagsmith with Grafana to send flag change events as annotations.

The video below demonstrates the integration process:

<ReactPlayer
    controls
    width="100%"
    height="460px"
    url='https://flagsmith.wistia.com/medias/z9vkon54qh' />

## Integration Setup

To set up the integration, follow these steps:

### In Grafana:

1. Go to Administration > Users and access > Service accounts.
2. Add a Service Account.
3. Set the Role to "Annotation Writer" or "Editor".
4. Click on "Add service account token" and save the generated token.

### In Flagsmith:

1. Go to Integrations and add the Grafana integration.
2. Enter the URL of your Grafana installation (e.g., `https://grafana.flagsmith.com`).
3. Paste the service account token from Grafana into the `Service account token` field.
4. Click Save.

Flag change events will now be sent to Grafana as _Organisation Level_ [Annotations](https://grafana.com/docs/grafana/latest/dashboards/build-dashboards/annotate-visualizations/).

To view the annotations in Grafana, go to Dashboard Settings > Annotations, select the `Grafana` data source, and filter by the `flagsmith` tag.

Annotations for feature-specific events include project tags, user-defined tags, and environment tags for flag change events.

## Feature Health Provider Setup

:::info

[Feature Health](/advanced-use/feature-health) is in Beta, please email support@flagsmith.com or chat with us <a href="#" class="open-chat" data-crisp-chat-message="Hello, I'm interested in joining the feature health beta.">here</a> if you'd like to join. 
:::

### In Flagsmith:

1. Go to Project Settings > Feature Health.
2. Select "Grafana" from the Provider Name drop-down menu.
3. Click Create and copy the Webhook URL.

### In Grafana:

1. Create a new Webhook contact point using the Webhook URL from Flagsmith. Refer to the [Grafana documentation on contact points](https://grafana.com/docs/grafana/latest/alerting/configure-notifications/manage-contact-points/#add-a-contact-point) for details.
2. Leave Optional Webhook settings empty. Ensure the "Disable resolved message" checkbox is unchecked.
3. Add the `flagsmith_feature` label to your alert rule, specifying the Flagsmith Feature name. Refer to the [Grafana documentation on alert rule labels](https://grafana.com/docs/grafana/latest/alerting/fundamentals/alert-rules/annotation-label/#labels) for more information.
4. Optionally, include the `flagsmith_environment` label in your alert rule, using the Flagsmith Environment name as the value.
5. Set the previously created contact point as the alert rule recipient.

You can create multiple alert rules pointing to the Feature Health Provider webhook. Ensure they include the `flagsmith_feature` label with a Feature name from the Project you created the Feature Health Provider for, to see Feature Health status changes for your features.

You can integrate Grafana Feature Health with Prometheus Alertmanager. For detailed instructions on adding Flagsmith labels to your alerts in Prometheus, refer to the [Prometheus Alertmanager webhook configuration](https://prometheus.io/docs/alerting/latest/configuration/#webhook_config) and [Alerting rules configuration](https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/#defining-alerting-rules) documentation.

The Feature Health UI will display the following information:
- Alert name
- Link to the alert instance in your Alertmanager
- Alert description (if provided in alert annotations)
- Alert summary (if provided in alert annotations)
- Dashboard URL (if Grafana)
- Panel URL (if Grafana)
- Runbook URL (if provided in alert annotations)
