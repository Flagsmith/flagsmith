import typing
from datetime import datetime

from pydantic import BaseModel


class GrafanaFeatureHealthEventReason(typing.TypedDict):
    alert_name: str
    generator_url: str
    description: typing.NotRequired[str]
    runbook_url: typing.NotRequired[str]
    summary: typing.NotRequired[str]


class GrafanaAlertInstance(BaseModel):
    annotations: dict[str, str]
    generatorURL: str
    endsAt: datetime
    fingerprint: str
    labels: dict[str, str]
    startsAt: datetime
    status: str


class GrafanaWebhookData(BaseModel):
    alerts: list[GrafanaAlertInstance]
