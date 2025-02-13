from dataclasses import dataclass
from datetime import datetime

from features.feature_health.models import FeatureHealthEventType


@dataclass
class FeatureHealthEventData:
    feature_name: str
    type: FeatureHealthEventType
    reason: str
    provider_name: str
    environment_name: str | None = None
    external_id: str | None = None
    created_at: datetime | None = None


@dataclass
class FeatureHealthProviderResponse:
    events: list[FeatureHealthEventData]
