import typing

from typing_extensions import TypedDict

from features.feature_health.types import FeatureHealthEventReason

GenericEventStatus: typing.TypeAlias = typing.Literal["healthy", "unhealthy"]


class GenericEvent(TypedDict):
    environment: typing.NotRequired[str]
    feature: str
    status: GenericEventStatus
    reason: typing.NotRequired[FeatureHealthEventReason]
