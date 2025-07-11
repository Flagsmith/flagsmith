---
title: Feature Health Metrics
sidebar_label: Feature Health Metrics
sidebar_position: 4
---

Feature Health enables you to monitor observability metrics within Flagsmith, specifically in relation to your Features and Environments. When your observability provider sends alert notifications, Flagsmith can mark Features (and optionally Environments) as **Unhealthy**, providing details about the alerts. This helps your team respond quickly and make informed decisions.

:::info

Feature Health is in Beta, please email support@flagsmith.com or chat with us <a href="#" class="open-chat" data-crisp-chat-message="Hello, I'm interested in joining the feature health beta.">here</a> if you'd like to join. 

:::

## Prerequisites

- You must have a supported observability provider (see below).
- You need admin access to your Flagsmith project settings.

---

## How to enable Feature Health

1. Go to your **Project Settings** in Flagsmith.
2. Navigate to the **Feature Health** section.
3. Choose your desired provider from the **Provider Name** drop-down menu (e.g., Grafana/Prometheus Alertmanager or Sample).
4. Click **Create** and copy the Webhook URL.

---

## How to integrate with Feature Health providers

### Grafana / Prometheus Alertmanager

[Learn more](/integrations/apm/grafana/#feature-health-provider-setup) about configuring Grafana / Prometheus Alertmanager Feature Health provider.

### Sample Provider

We provide a Sample Provider for your custom integrations. To create a Sample Feature Health webhook:

1. Go to Project Settings > Feature Health.
2. Select "Sample" from the Provider Name drop-down menu.
3. Click Create and copy the Webhook URL.

You can use the webhook in your custom integration. Refer to the payload schema below:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "SampleEvent",
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

- For more on observability integrations, see the [Integrations documentation](/integrations/).
- Need help or want to join the Beta? Contact [support@flagsmith.com](mailto:support@flagsmith.com) or chat with us in-app.
