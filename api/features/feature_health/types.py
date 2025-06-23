import typing
from dataclasses import dataclass
from datetime import datetime

from typing_extensions import TypedDict

if typing.TYPE_CHECKING:
    from features.feature_health.models import FeatureHealthEventType


class FeatureHealthEventReasonTextBlock(TypedDict):
    text: str
    title: typing.NotRequired[str]


class FeatureHealthEventReasonUrlBlock(TypedDict):
    url: str
    title: typing.NotRequired[str]


class FeatureHealthEventReason(TypedDict):
    text_blocks: list[FeatureHealthEventReasonTextBlock]
    url_blocks: list[FeatureHealthEventReasonUrlBlock]


@dataclass
class FeatureHealthEventData:
    feature_name: str
    type: "FeatureHealthEventType"
    provider_name: str
    reason: FeatureHealthEventReason | None = None
    environment_name: str | None = None
    external_id: str | None = None
    created_at: datetime | None = None


@dataclass
class FeatureHealthProviderResponse:
    events: list[FeatureHealthEventData]
