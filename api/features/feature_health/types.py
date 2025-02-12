from dataclasses import dataclass

from features.feature_health.models import FeatureHealthEventType


@dataclass
class FeatureHealthProviderResponse:
    feature_name: str
    environment_name: str | None
    event_type: FeatureHealthEventType
    reason: str
