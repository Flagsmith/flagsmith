---
title: Feature Health Metrics
sidebar_label: Feature Health Metrics
sidebar_position: 4
---

Feature health enables you to monitor observability metrics within Flagsmith, specifically in relation to your features and environments. When your observability provider sends alert notifications, Flagsmith can mark features (and optionally environments) as **unhealthy**, providing details about the alerts. This assists your team in responding quickly and making informed decisions.

## Prerequisites

- You must have a supported observability provider (see below).
- You need admin access to your Flagsmith project settings.

---

## How to enable Feature Health

1. Go to your **Project Settings** in Flagsmith.
2. Navigate to the **Feature Health** section.
3. Choose your desired provider from the **Provider Name** drop-down menu (e.g., Grafana/Prometheus Alertmanager or Webhook).
4. Click **Create** and copy the webhook URL.

---

## How to integrate with Feature Health providers

### Grafana / Prometheus Alertmanager

[Learn more](/third-party-integrations/observability-and-monitoring/grafana) about configuring Grafana / Prometheus Alertmanager feature health provider.

### Webhook Provider

We provide a Webhook Provider for your custom integrations. To create a Webhook Feature Health webhook:

1. Go to Project Settings > Feature Health.
2. Select "Webhook" from the Provider Name drop-down menu.
3. Click Create and copy the webhook URL.

You can use the webhook in your custom integration. Refer to the payload schema below:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "WebhookEvent",
  "type": "object",
  "properties": {
    "environment": {
      "type": "string"
    },
    "feature": {
      "type": "string"
    },
    "status": {
      "type": "string",
      "enum": ["healthy", "unhealthy"]
    },
    "reason": {
      "$ref": "#/definitions/FeatureHealthEventReason"
    }
  },
  "required": ["feature", "status"],
  "definitions": {
    "FeatureHealthEventReason": {
      "type": "object",
      "properties": {
        "text_blocks": {
          "type": "array",
          "items": {
            "$ref": "#/definitions/FeatureHealthEventReasonTextBlock"
          }
        },
        "url_blocks": {
          "type": "array",
          "items": {
            "$ref": "#/definitions/FeatureHealthEventReasonUrlBlock"
          }
        }
      }
    },
    "FeatureHealthEventReasonTextBlock": {
      "type": "object",
      "properties": {
        "text": {
          "type": "string"
        },
        "title": {
          "type": "string"
        }
      },
      "required": ["text"]
    },
    "FeatureHealthEventReasonUrlBlock": {
      "type": "object",
      "properties": {
        "url": {
          "type": "string"
        },
        "title": {
          "type": "string"
        }
      },
      "required": ["url"]
    }
  }
}
```

---

## What's next?

- For more on observability integrations, see the [observability integrations](/third-party-integrations/observability-and-monitoring/grafana).
- Need help or want to join the Beta? Contact [support@flagsmith.com](mailto:support@flagsmith.com) or chat with us in-app.
