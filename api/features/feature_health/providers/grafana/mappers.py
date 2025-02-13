import json

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
    GrafanaFeatureHealthEventReason,
    GrafanaWebhookData,
)
from features.feature_health.types import FeatureHealthEventData


def map_payload_to_alert_instances(payload: str) -> list[GrafanaAlertInstance]:
    webhook_data = GrafanaWebhookData.model_validate_json(payload)

    return webhook_data.alerts


def map_alert_instance_to_feature_health_event_reason(
    alert_instance: GrafanaAlertInstance,
) -> str:
    reason_data: GrafanaFeatureHealthEventReason = {}

    annotations = alert_instance.annotations

    for key in (
        "description",
        "runbook_url",
        "summary",
    ):
        if value := annotations.get(key):
            reason_data[key] = value

    reason_data["alert_name"] = alert_instance.labels.get("alertname") or ""
    reason_data["generator_url"] = alert_instance.generatorURL

    return json.dumps(reason_data)


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
