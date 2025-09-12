from features.feature_health.providers.sample.mappers import (
    map_payload_to_provider_response,
)
from features.feature_health.types import FeatureHealthProviderResponse


def get_provider_response(payload: str) -> FeatureHealthProviderResponse:
    return map_payload_to_provider_response(payload)
