from features.feature_health.models import (
    FeatureHealthEventType,
    FeatureHealthProviderName,
)
from features.feature_health.providers.grafana.constants import (
    GRAFANA_ENVIRONMENT_LABEL_NAME,
    GRAFANA_FEATURE_LABEL_NAME,
)
from features.feature_health.providers.grafana.types import (
    GrafanaAlertInstance,
    GrafanaWebhookData,
)
from features.feature_health.types import (
    FeatureHealthEventData,
    FeatureHealthEventReason,
)


def map_payload_to_alert_instances(payload: str) -> list[GrafanaAlertInstance]:
    webhook_data = GrafanaWebhookData.model_validate_json(payload)

    return webhook_data.alerts


def map_alert_instance_to_feature_health_event_reason(
    alert_instance: GrafanaAlertInstance,
) -> FeatureHealthEventReason:
    reason_data: FeatureHealthEventReason = {"text_blocks": [], "url_blocks": []}

    annotations = alert_instance.annotations

    # Populate text blocks.
    alert_name = alert_instance.labels.get("alertname") or "Alertmanager Alert"
    description = annotations.get("description") or ""
    reason_data["text_blocks"].append(
        {
            "title": alert_name,
            "text": description,
        }
    )
    if summary := annotations.get("summary"):
        reason_data["text_blocks"].append(
            {
                "title": "Summary",
                "text": summary,
            }
        )

    # Populate URL blocks.
    reason_data["url_blocks"].append(
        {"title": "Alert", "url": alert_instance.generatorURL}
    )
    if dashboard_url := alert_instance.dashboardURL:
        reason_data["url_blocks"].append({"title": "Dashboard", "url": dashboard_url})
    if panel_url := alert_instance.panelURL:
        reason_data["url_blocks"].append({"title": "Panel", "url": panel_url})
    if runbook_url := annotations.get("runbook_url"):
        reason_data["url_blocks"].append({"title": "Runbook", "url": runbook_url})

    return reason_data


def map_alert_instance_to_feature_health_event_data(
    alert_instance: GrafanaAlertInstance,
) -> FeatureHealthEventData | None:
    labels = alert_instance.labels
    if feature_name := labels.get(GRAFANA_FEATURE_LABEL_NAME):
        if alert_instance.status == "firing":
            created_at = alert_instance.startsAt
            event_type = FeatureHealthEventType.UNHEALTHY
        else:
            created_at = alert_instance.endsAt
            event_type = FeatureHealthEventType.HEALTHY
        return FeatureHealthEventData(
            created_at=created_at,
            feature_name=feature_name,
            environment_name=labels.get(GRAFANA_ENVIRONMENT_LABEL_NAME),
            type=event_type,
            external_id=alert_instance.fingerprint,
            reason=map_alert_instance_to_feature_health_event_reason(alert_instance),
            provider_name=FeatureHealthProviderName.GRAFANA.value,
        )
    return None
