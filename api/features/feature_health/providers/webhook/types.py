import typing

from typing_extensions import TypedDict

from features.feature_health.types import (
    FeatureHealthEventReasonTextBlock,
    FeatureHealthEventReasonUrlBlock,
)

WebhookEventStatus: typing.TypeAlias = typing.Literal["healthy", "unhealthy"]


class WebhookEventReason(TypedDict):
    text_blocks: typing.NotRequired[list[FeatureHealthEventReasonTextBlock]]
    url_blocks: typing.NotRequired[list[FeatureHealthEventReasonUrlBlock]]


class WebhookEvent(TypedDict):
    environment: typing.NotRequired[str]
    feature: str
    status: WebhookEventStatus
    reason: typing.NotRequired[WebhookEventReason]
