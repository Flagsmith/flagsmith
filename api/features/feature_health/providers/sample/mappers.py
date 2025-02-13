from pydantic.type_adapter import TypeAdapter

from features.feature_health.models import (
    FeatureHealthEventType,
    FeatureHealthProviderName,
)
from features.feature_health.providers.sample.types import (
    SampleEvent,
    SampleEventStatus,
)
from features.feature_health.types import (
    FeatureHealthEventData,
    FeatureHealthProviderResponse,
)

_sample_event_type_adapter = TypeAdapter(SampleEvent)


def map_sample_event_status_to_feature_health_event_type(
    status: SampleEventStatus,
) -> FeatureHealthEventType:
    return (
        FeatureHealthEventType.UNHEALTHY
        if status == "unhealthy"
        else FeatureHealthEventType.HEALTHY
    )


def map_payload_to_provider_response(
    payload: str,
) -> FeatureHealthProviderResponse:
    event_data: SampleEvent = _sample_event_type_adapter.validate_json(payload)

    return FeatureHealthProviderResponse(
        events=[
            FeatureHealthEventData(
                feature_name=event_data["feature"],
                environment_name=event_data.get("environment"),
                type=map_sample_event_status_to_feature_health_event_type(
                    event_data["status"]
                ),
                reason=(
                    event_data.get("reason") or {"text_blocks": [], "url_blocks": []}
                ),
                provider_name=FeatureHealthProviderName.SAMPLE.value,
            ),
        ],
    )
