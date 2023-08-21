import enum
import json
import typing
from typing import Type, Union

import backoff
import requests
from core.constants import FLAGSMITH_SIGNATURE_HEADER
from core.signing import sign_payload
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.serializers.json import DjangoJSONEncoder
from django.template.loader import get_template

from environments.models import Environment, Webhook
from organisations.models import OrganisationWebhook
from projects.models import Organisation
from task_processor.decorators import register_task_handler
from webhooks.sample_webhook_data import (
    environment_webhook_data,
    organisation_webhook_data,
)

from .models import AbstractBaseExportableWebhookModel
from .serializers import WebhookSerializer

if typing.TYPE_CHECKING:
    import environments  # noqa

WebhookModels = typing.Union[OrganisationWebhook, Webhook]


class WebhookEventType(enum.Enum):
    FLAG_UPDATED = "FLAG_UPDATED"
    FLAG_DELETED = "FLAG_DELETED"
    AUDIT_LOG_CREATED = "AUDIT_LOG_CREATED"


class WebhookType(enum.Enum):
    ORGANISATION = "ORGANISATION"
    ENVIRONMENT = "ENVIRONMENT"


WEBHOOK_SAMPLE_DATA = {
    WebhookType.ORGANISATION: organisation_webhook_data,
    WebhookType.ENVIRONMENT: environment_webhook_data,
}


def get_webhook_model(
    webhook_type: WebhookType,
) -> Type[Union[OrganisationWebhook, Webhook]]:
    if webhook_type == WebhookType.ORGANISATION:
        return OrganisationWebhook
    if webhook_type == WebhookType.ENVIRONMENT:
        return Webhook


@register_task_handler()
def call_environment_webhooks(
    environment_id: int, data: typing.Mapping, event_type: str
):
    if settings.DISABLE_WEBHOOKS:
        return
    try:
        environment = Environment.objects.get(id=environment_id)
    except Environment.DoesNotExist:
        return
    _call_webhooks(
        (webhook.id for webhook in environment.webhooks.filter(enabled=True)),
        data,
        event_type,
        WebhookType.ENVIRONMENT,
    )


@register_task_handler()
def call_organisation_webhooks(
    organisation_id: int, data: typing.Mapping, event_type: str
):
    if settings.DISABLE_WEBHOOKS:
        return
    try:
        organisation = Organisation.objects.get(id=organisation_id)
    except Organisation.DoesNotExist:
        return
    _call_webhooks(
        (webhook.id for webhook in organisation.webhooks.filter(enabled=True)),
        data,
        event_type,
        WebhookType.ORGANISATION,
    )


def call_integration_webhook(config, data):
    return _call_webhook(config, data)


def trigger_sample_webhook(
    webhook: typing.Type[AbstractBaseExportableWebhookModel], webhook_type: WebhookType
) -> requests.models.Response:
    data = WEBHOOK_SAMPLE_DATA.get(webhook_type)
    serializer = WebhookSerializer(data=data)
    serializer.is_valid(raise_exception=True)

    return _call_webhook(webhook, serializer.data)


@backoff.on_exception(
    backoff.expo,
    requests.exceptions.RequestException,
    max_tries=3,
    jitter=backoff.full_jitter,
)
def _call_webhook(
    webhook: typing.Type[AbstractBaseExportableWebhookModel],
    data: typing.Mapping,
) -> requests.models.Response:
    headers = {"content-type": "application/json"}
    json_data = json.dumps(data, sort_keys=True, cls=DjangoJSONEncoder)
    if webhook.secret:
        signature = sign_payload(json_data, key=webhook.secret)
        headers.update({FLAGSMITH_SIGNATURE_HEADER: signature})

    return requests.post(str(webhook.url), data=json_data, headers=headers, timeout=10)


@register_task_handler()
def _call_webhook_email_on_error(
    webhook_id: int, data: typing.Mapping, webhook_type: str
):
    if webhook_type == WebhookType.ORGANISATION.value:
        webhook = OrganisationWebhook.objects.get(id=webhook_id)
    else:
        webhook = Webhook.objects.get(id=webhook_id)
    try:
        res = _call_webhook(webhook, data)
    except requests.exceptions.RequestException as exc:
        send_failure_email(
            webhook,
            data,
            webhook_type,
            f"N/A ({exc.__class__.__name__})",
        )
        return

    if res.status_code != 200:
        send_failure_email(webhook, data, webhook_type, res.status_code)


def _call_webhooks(
    webhook_ids: typing.Iterable[int],
    data: typing.Mapping,
    event_type: str,
    webhook_type: WebhookType,
):
    webhook_data = {"event_type": event_type, "data": data}
    serializer = WebhookSerializer(data=webhook_data)
    serializer.is_valid(raise_exception=False)
    for webhook_id in webhook_ids:
        _call_webhook_email_on_error.delay(
            args=(webhook_id, serializer.data, webhook_type.value)
        )


def send_failure_email(
    webhook: WebhookModels,
    data: typing.Mapping,
    webhook_type: str,
    status_code: typing.Union[int, str] = None,
):
    template_data = _get_failure_email_template_data(
        webhook, data, webhook_type, status_code
    )
    organisation = (
        webhook.organisation
        if webhook_type == WebhookType.ORGANISATION.value
        else webhook.environment.project.organisation
    )

    text_template = get_template("features/webhook_failure.txt")
    text_content = text_template.render(template_data)
    subject = "Flagsmith Webhook Failure"
    msg = EmailMultiAlternatives(
        subject,
        text_content,
        settings.EMAIL_CONFIGURATION.get("INVITE_FROM_EMAIL"),
        [organisation.webhook_notification_email],
    )
    msg.content_subtype = "plain"
    msg.send()


def _get_failure_email_template_data(
    webhook: WebhookModels,
    data: typing.Mapping,
    webhook_type: str,
    status_code: typing.Union[int, str] = None,
):
    data = {
        "status_code": status_code,
        "data": json.dumps(data, sort_keys=True, indent=2, cls=DjangoJSONEncoder),
        "webhook_url": webhook.url,
    }

    if webhook_type == WebhookType.ENVIRONMENT.value:
        data["project_name"] = webhook.environment.project.name
        data["environment_name"] = webhook.environment.name

    return data
