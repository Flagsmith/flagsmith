import typing

from typing_extensions import TypedDict

from features.feature_health.types import FeatureHealthEventReason

SampleEventStatus: typing.TypeAlias = typing.Literal["healthy", "unhealthy"]


class SampleEvent(TypedDict):
    environment: typing.NotRequired[str]
    feature: str
    status: SampleEventStatus
    reason: typing.NotRequired[FeatureHealthEventReason]
