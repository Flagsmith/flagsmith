from features.feature_health.providers.grafana.mappers import (
    map_alert_instance_to_feature_health_event_data,
    map_payload_to_alert_instances,
)
from features.feature_health.types import (
    FeatureHealthEventData,
    FeatureHealthProviderResponse,
)


def get_provider_response(payload: str) -> FeatureHealthProviderResponse:
    events: list[FeatureHealthEventData] = []

    for alert_instance in map_payload_to_alert_instances(payload):
        if event_data := map_alert_instance_to_feature_health_event_data(
            alert_instance
        ):
            events.append(event_data)

    return FeatureHealthProviderResponse(events=events)
