from datetime import datetime

from pydantic import BaseModel


class AlertmanagerAlertInstance(BaseModel):
    annotations: dict[str, str]
    generatorURL: str
    endsAt: datetime
    fingerprint: str
    labels: dict[str, str]
    startsAt: datetime
    status: str


class GrafanaAlertInstance(AlertmanagerAlertInstance):
    dashboardURL: str = ""
    panelURL: str = ""
    silenceURL: str = ""


class GrafanaWebhookData(BaseModel):
    alerts: list[GrafanaAlertInstance]
