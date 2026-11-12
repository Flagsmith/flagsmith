---
title: Prometheus Integration
description: Integrate Flagsmith with Prometheus Alertmanager
sidebar_label: Prometheus
hide_title: true
---

Integrate Flagsmith with Prometheus Alertmanager to drive [Feature Health](/managing-flags/feature-health-metrics) status from your existing alerts.

## Feature Health Provider Setup

### In Flagsmith

1. Go to Project Settings > Feature Health.
2. Select "Grafana" from the Provider Name drop-down menu.
3. Click Create and copy the Webhook URL.

:::note

The Feature Health webhook accepts the Alertmanager payload format, so "Grafana" is the right choice here whether you're sending alerts via Grafana or directly from Prometheus Alertmanager.

:::

### In Alertmanager

Add a webhook receiver pointing at the Flagsmith Webhook URL, and ensure your alert rules carry the `flagsmith_feature` label (and optionally `flagsmith_environment`).

```yaml
# alertmanager.yml
receivers:
  - name: flagsmith-feature-health
    webhook_configs:
      - url: <FLAGSMITH_WEBHOOK_URL>
        send_resolved: true
```

```yaml
# example alert rule
groups:
  - name: flagsmith-feature-health
    rules:
      - alert: HighErrorRate
        expr: ...
        labels:
          flagsmith_feature: my_feature_name
          flagsmith_environment: production
        annotations:
          summary: ...
          description: ...
          runbook_url: ...
```

Refer to the [Alertmanager webhook configuration](https://prometheus.io/docs/alerting/latest/configuration/#webhook_config) and [Alerting rules configuration](https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/#defining-alerting-rules) documentation for full details.

## What the Feature Health UI displays

- Alert name
- Link to the alert instance in Alertmanager
- Alert description (if provided in annotations)
- Alert summary (if provided in annotations)
- Runbook URL (if provided in annotations)
