import enum
import json
import typing
from datetime import datetime, timedelta
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
        environment.webhooks.filter(enabled=True),
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
        organisation.webhooks.filter(enabled=True),
        data,
        event_type,
        WebhookType.ORGANISATION,
    )


def call_integration_webhook(config, data):
    return _call_webhook_sync(config, data)


def trigger_sample_webhook(
    webhook: WebhookModels, webhook_type: WebhookType
) -> requests.models.Response:
    data = WEBHOOK_SAMPLE_DATA.get(webhook_type)
    serializer = WebhookSerializer(data=data)
    serializer.is_valid(raise_exception=True)

    return _call_webhook_sync(webhook, serializer.data)


@backoff.on_exception(
    backoff.expo,
    requests.exceptions.RequestException,
    max_tries=3,
    jitter=backoff.full_jitter,
)
def _call_webhook_sync(
    webhook: WebhookModels,
    data: typing.Mapping,
) -> requests.models.Response:
    headers = {"content-type": "application/json"}
    json_data = json.dumps(data, sort_keys=True, cls=DjangoJSONEncoder)
    if webhook.secret:
        signature = sign_payload(json_data, key=webhook.secret)
        headers.update({FLAGSMITH_SIGNATURE_HEADER: signature})

    return requests.post(str(webhook.url), data=json_data, headers=headers, timeout=10)


def _call_webhook_async(
    webhook: WebhookModels,
    data: typing.Mapping,
    webhook_type: WebhookType,
    max_tries: int = 3,
    send_error_email: bool = False,
    backoff_type: typing.Union[
        backoff.constant, backoff.expo, backoff.fibo
    ] = backoff.expo,
    jitter_type: typing.Union[
        backoff.random_jitter, backoff.full_jitter
    ] = backoff.full_jitter,
) -> None:
    @register_task_handler()
    def _setup_call_webhook_task(
        webhook_id: int,
        data: typing.Mapping,
        webhook_type: str,
        try_count: int = 0,
        max_tries: int = 3,
        send_error_email: bool = False,
        backoff_type: str = backoff.expo.__name__,
        jitter_type: str = backoff.full_jitter.__name__,
    ):
        if try_count >= max_tries:
            return

        headers = {"content-type": "application/json"}
        json_data = json.dumps(data, sort_keys=True, cls=DjangoJSONEncoder)
        if webhook_type == WebhookType.ORGANISATION.value:
            webhook = OrganisationWebhook.objects.get(id=webhook_id)
        else:
            webhook = Webhook.objects.get(id=webhook_id)

        if webhook.secret:
            signature = sign_payload(json_data, key=webhook.secret)
            headers.update({FLAGSMITH_SIGNATURE_HEADER: signature})

        try:
            res = requests.post(
                str(webhook.url), data=json_data, headers=headers, timeout=10
            )
        except requests.exceptions.RequestException as exc:
            # Increase the try count first
            try_count += 1

            # Don't schedule a task if the try_count will exceed max_tries,
            # fail the backoff and send a failure email
            if send_error_email and try_count == max_tries:
                send_failure_email(
                    webhook,
                    data,
                    webhook_type,
                    f"N/A ({exc.__class__.__name__})",
                )
            else:
                wait_seconds = _calculate_wait_time(
                    backoff_type, jitter_type, try_count
                )

                _setup_call_webhook_task.delay(
                    delay_until=datetime.now() + timedelta(seconds=wait_seconds),
                    args=(
                        webhook_id,
                        data,
                        webhook_type,
                        try_count,
                        max_tries,
                        send_error_email,
                        backoff_type,
                        jitter_type,
                    ),
                )
            return

        if res.status_code != 200 and send_error_email:
            send_failure_email(webhook, data, webhook_type, res.status_code)

    _setup_call_webhook_task.delay(
        args=(
            webhook.id,
            data,
            webhook_type.value,
            0,
            max_tries,
            send_error_email,
            backoff_type.__name__,
            jitter_type.__name__,
        )
    )


def _calculate_wait_time(backoff_type, jitter_type, try_count) -> float:
    """
    Calculate the wait time for the next retry, based on the current try count
    and the backoff and jitter types.
    """

    if backoff.constant.__name__ == backoff_type:
        backoff_fn = backoff.constant
    elif backoff.fibo.__name__ == backoff_type:
        backoff_fn = backoff.fibo
    else:
        backoff_fn = backoff.expo

    # Create a backoff generator
    gen = backoff_fn()

    delay_time = 0

    # Move the generator try_count times forward, as we can't store the generator
    # state in the task_processor
    for _ in range(try_count):
        delay_time = next(gen)

    if backoff.random_jitter.__name__ == jitter_type:
        delay_time = backoff.random_jitter(delay_time)
    else:
        delay_time += backoff.full_jitter(delay_time)

    return delay_time


@register_task_handler()
def call_webhook_email_on_error(
    webhook_id: int, data: typing.Mapping, webhook_type: str
):
    if webhook_type == WebhookType.ORGANISATION.value:
        webhook = OrganisationWebhook.objects.get(id=webhook_id)
    else:
        webhook = Webhook.objects.get(id=webhook_id)

    _call_webhook_async(
        webhook,
        data,
        WebhookType.ENVIRONMENT
        if WebhookType.ENVIRONMENT.value == webhook_type
        else WebhookType.ORGANISATION,
        max_tries=3,
        send_error_email=True,
    )


def _call_webhooks(
    webhooks: typing.Iterable[WebhookModels],
    data: typing.Mapping,
    event_type: str,
    webhook_type: WebhookType,
):
    webhook_data = {"event_type": event_type, "data": data}
    serializer = WebhookSerializer(data=webhook_data)
    serializer.is_valid(raise_exception=False)
    for webhook in webhooks:
        call_webhook_email_on_error.delay(
            args=(webhook.id, serializer.data, webhook_type.value)
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
