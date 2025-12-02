import typing

from typing_extensions import TypedDict

from features.feature_health.types import FeatureHealthEventReason

WebhookEventStatus: typing.TypeAlias = typing.Literal["healthy", "unhealthy"]


class WebhookEvent(TypedDict):
    environment: typing.NotRequired[str]
    feature: str
    status: WebhookEventStatus
    reason: typing.NotRequired[FeatureHealthEventReason]
