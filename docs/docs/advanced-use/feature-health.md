---
title: Feature Health
---

:::info

Feature Health is an upcoming feature that's not yet available.

:::

Feature Health enables users to monitor observability metrics within Flagsmith, specifically in relation to Flagsmith's Features and Environments. Flagsmith receives alert notifications from your observability provider and, based on this data, marks your Features and optionally Environments with an **Unhealthy** status, providing details about the alerts. This enhances your team's observability, allowing for quicker, more informed decisions.

## Integrations

The following is an overview of the Feature Health providers currently supported.

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
