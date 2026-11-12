import json
import typing

import pydantic

from features.feature_health.models import FeatureHealthEvent
from features.feature_health.types import FeatureHealthEventData

if typing.TYPE_CHECKING:
    from environments.models import Environment
    from features.models import Feature


def map_feature_health_event_data_to_feature_health_event(
    *,
    feature_health_event_data: FeatureHealthEventData,
    feature: "Feature",
    environment: "Environment | None",
) -> FeatureHealthEvent:
    if reason := feature_health_event_data.reason:
        instance_reason = json.dumps(reason)
    else:
        instance_reason = None
    instance = FeatureHealthEvent(
        feature=feature,
        environment=environment,
        type=feature_health_event_data.type.value,
        reason=instance_reason,
        external_id=feature_health_event_data.external_id,
        provider_name=feature_health_event_data.provider_name,
    )
    if feature_health_event_data.created_at:
        instance.created_at = feature_health_event_data.created_at
    return instance


def map_validation_error_to_payload_error_details(
    exc: pydantic.ValidationError,
) -> list[dict[str, str]]:
    # Inputs are deliberately omitted so as not to echo large payloads back.
    return [
        {
            "loc": ".".join(str(part) for part in error["loc"]),
            "msg": error["msg"],
            "type": error["type"],
        }
        for error in exc.errors(
            include_url=False,
            include_context=False,
            include_input=False,
        )
    ]
