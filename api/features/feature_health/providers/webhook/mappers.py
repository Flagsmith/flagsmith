from pydantic.type_adapter import TypeAdapter

from features.feature_health.models import (
    FeatureHealthEventType,
    FeatureHealthProviderName,
)
from features.feature_health.providers.webhook.types import (
    WebhookEvent,
    WebhookEventReason,
    WebhookEventStatus,
)
from features.feature_health.types import (
    FeatureHealthEventData,
    FeatureHealthEventReason,
    FeatureHealthProviderResponse,
)

_sample_event_type_adapter = TypeAdapter(WebhookEvent)


def map_sample_event_status_to_feature_health_event_type(
    status: WebhookEventStatus,
) -> FeatureHealthEventType:
    return (
        FeatureHealthEventType.UNHEALTHY
        if status == "unhealthy"
        else FeatureHealthEventType.HEALTHY
    )


def map_webhook_event_reason_to_feature_health_event_reason(
    reason: WebhookEventReason,
) -> FeatureHealthEventReason:
    return {
        "text_blocks": reason.get("text_blocks", []),
        "url_blocks": reason.get("url_blocks", []),
    }


def map_payload_to_provider_response(
    payload: str,
) -> FeatureHealthProviderResponse:
    event_data: WebhookEvent = _sample_event_type_adapter.validate_json(payload)
    reason = event_data.get("reason")

    return FeatureHealthProviderResponse(
        events=[
            FeatureHealthEventData(
                feature_name=event_data["feature"],
                environment_name=event_data.get("environment"),
                type=map_sample_event_status_to_feature_health_event_type(
                    event_data["status"]
                ),
                reason=(
                    map_webhook_event_reason_to_feature_health_event_reason(reason)
                    if reason is not None
                    else None
                ),
                provider_name=FeatureHealthProviderName.WEBHOOK.value,
            ),
        ],
    )
