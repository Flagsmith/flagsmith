import enum
import json
import logging
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
from django.utils import timezone

from environments.models import Environment, Webhook
from organisations.models import OrganisationWebhook
from projects.models import Organisation
from task_processor.decorators import register_task_handler
from task_processor.task_run_method import TaskRunMethod
from webhooks.sample_webhook_data import (
    environment_webhook_data,
    organisation_webhook_data,
)

from .models import AbstractBaseWebhookModel
from .serializers import WebhookSerializer

if typing.TYPE_CHECKING:
    import environments  # noqa

logger = logging.getLogger(__name__)
WebhookModels = typing.Union[OrganisationWebhook, Webhook]


class WebhookEventType(enum.Enum):
    FLAG_UPDATED = "FLAG_UPDATED"
    FLAG_DELETED = "FLAG_DELETED"
    AUDIT_LOG_CREATED = "AUDIT_LOG_CREATED"
    NEW_VERSION_PUBLISHED = "NEW_VERSION_PUBLISHED"
    FEATURE_EXTERNAL_RESOURCE_ADDED = "FEATURE_EXTERNAL_RESOURCE_ADDED"
    FEATURE_EXTERNAL_RESOURCE_REMOVED = "FEATURE_EXTERNAL_RESOURCE_REMOVED"


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
    environment_id: int,
    data: typing.Mapping,
    event_type: str,
    retries: int = settings.WEBHOOK_BACKOFF_RETRIES,
):
    """
    Call environment webhooks.

    :param environment_id: The ID of the environment for which webhooks will be triggered.
    :param data: A mapping containing the data to be sent in the webhook request.
    :param event_type: The type of event to trigger the webhook.
    :param retries: The number of times to retry the webhook in case of failure (int, default is 3).
    """

    if settings.DISABLE_WEBHOOKS:
        return
    try:
        environment = Environment.objects.get(id=environment_id)
    except Environment.DoesNotExist:
        return
    _call_webhooks(
        environment.webhooks.filter(enabled=True),
        data,
        event_type,
        WebhookType.ENVIRONMENT,
        retries,
    )


@register_task_handler()
def call_organisation_webhooks(
    organisation_id: int,
    data: typing.Mapping,
    event_type: str,
    retries: int = settings.WEBHOOK_BACKOFF_RETRIES,
):
    """
    Call organisation webhooks.

    :param organisation_id: The ID of the organisation for which webhooks will be triggered.
    :param data: A mapping containing the data to be sent in the webhook request.
    :param event_type: The type of event to trigger the webhook.
    :param retries: The number of times to retry the webhook in case of failure (int, default is 3).
    """

    if settings.DISABLE_WEBHOOKS:
        return
    try:
        organisation = Organisation.objects.get(id=organisation_id)
    except Organisation.DoesNotExist:
        return
    _call_webhooks(
        organisation.webhooks.filter(enabled=True),
        data,
        event_type,
        WebhookType.ORGANISATION,
        retries,
    )


def call_integration_webhook(config: AbstractBaseWebhookModel, data: typing.Mapping):
    return _call_webhook(config, data)


def trigger_sample_webhook(
    webhook: AbstractBaseWebhookModel, webhook_type: WebhookType
) -> requests.models.Response:
    data = WEBHOOK_SAMPLE_DATA.get(webhook_type)
    serializer = WebhookSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    """
    :raises requests.exceptions.RequestException: If an error occurs while making the request to the webhook.
    """
    return _call_webhook(webhook, serializer.data)


@backoff.on_exception(
    wait_gen=backoff.expo,
    exception=requests.exceptions.RequestException,
    max_tries=settings.WEBHOOK_BACKOFF_RETRIES,
    raise_on_giveup=False,
    giveup_log_level=logging.WARNING,
)
def _call_webhook(
    webhook: AbstractBaseWebhookModel,
    data: typing.Mapping,
) -> requests.models.Response:
    headers = {"content-type": "application/json"}
    json_data = json.dumps(data, sort_keys=True, cls=DjangoJSONEncoder)
    if webhook.secret:
        signature = sign_payload(json_data, key=webhook.secret)
        headers.update({FLAGSMITH_SIGNATURE_HEADER: signature})

    try:
        res = requests.post(
            str(webhook.url), data=json_data, headers=headers, timeout=10
        )
        res.raise_for_status()
        return res
    except requests.exceptions.RequestException as exc:
        logger.debug("Error calling webhook", exc_info=exc)
        raise


@register_task_handler()
def call_webhook_with_failure_mail_after_retries(
    webhook_id: int,
    data: typing.Mapping,
    webhook_type: str,
    send_failure_mail: bool = False,
    max_retries: int = settings.WEBHOOK_BACKOFF_RETRIES,
    try_count: int = 1,
):
    """
    Call a webhook with support for sending failure emails after retries.

    :param webhook_id: The ID of the webhook to be called.
    :param data: A mapping containing the data to be sent in the webhook request.
    :param webhook_type: The type of the webhook to be triggered.
    :param send_failure_mail: Whether to send a failure notification email (bool, default is False).
    :param max_retries: The maximum number of retries to attempt (int, default is 3).
    :param try_count: Stores the current retry attempt count in scheduled tasks,
                        not needed to be specified (int, default is 1).
    """

    if try_count > max_retries:
        raise ValueError("try_count can't be greater than max_retries")

    if webhook_type == WebhookType.ORGANISATION.value:
        webhook = OrganisationWebhook.objects.get(id=webhook_id)
    else:
        webhook = Webhook.objects.get(id=webhook_id)

    headers = {"content-type": "application/json"}
    json_data = json.dumps(data, sort_keys=True, cls=DjangoJSONEncoder)
    if webhook.secret:
        signature = sign_payload(json_data, key=webhook.secret)
        headers.update({FLAGSMITH_SIGNATURE_HEADER: signature})

    try:
        res = requests.post(
            str(webhook.url), data=json_data, headers=headers, timeout=10
        )
        res.raise_for_status()
    except requests.exceptions.RequestException as exc:
        if try_count == max_retries or not settings.RETRY_WEBHOOKS:
            if send_failure_mail:
                send_failure_email(
                    webhook,
                    data,
                    webhook_type,
                    f"{f'HTTP {exc.response.status_code}' if exc.response else 'N/A'} ({exc.__class__.__name__})",
                )
        else:
            call_webhook_with_failure_mail_after_retries.delay(
                delay_until=(
                    timezone.now()
                    + timezone.timedelta(
                        seconds=settings.WEBHOOK_BACKOFF_BASE**try_count
                    )
                    if settings.TASK_RUN_METHOD == TaskRunMethod.TASK_PROCESSOR
                    else None
                ),
                args=(
                    webhook_id,
                    data,
                    webhook_type,
                    send_failure_mail,
                    max_retries,
                    try_count + 1,
                ),
            )
        return
    return res


def _call_webhooks(
    webhooks: typing.Iterable[WebhookModels],
    data: typing.Mapping,
    event_type: str,
    webhook_type: WebhookType,
    retries: int = settings.WEBHOOK_BACKOFF_RETRIES,
):
    webhook_data = {"event_type": event_type, "data": data}
    serializer = WebhookSerializer(data=webhook_data)
    serializer.is_valid(raise_exception=False)
    for webhook in webhooks:
        call_webhook_with_failure_mail_after_retries.delay(
            args=(webhook.id, serializer.data, webhook_type.value, True, retries)
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
