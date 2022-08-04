import typing

from environments.models import Environment
from features.models import Feature
from features.tasks import date_format
from task_processor.decorators import register_task_handler
from users.models import FFAdminUser
from webhooks.webhooks import WebhookEventType, call_environment_webhooks


@register_task_handler()
def call_environment_webhook(
    feature_id: int,
    environment_id: int,
    identity_id: typing.Union[id, str],
    identity_identifier: str,
    changed_by_user_id: int,
    new_enabled_state: bool,
    new_value: typing.Union[bool, int, str],
    previous_enabled_state: bool = None,
    previous_value: typing.Union[bool, int, str] = None,
):
    feature = Feature.objects.get(id=feature_id)
    environment = Environment.objects.get(id=environment_id)
    changed_by = FFAdminUser.objects.get(id=changed_by_user_id)

    # TODO: refactor this to a common location (ideally use a serializer)
    default_data = {
        "feature": {
            "id": feature.id,
            "created_date": feature.created_date.strftime(
                date_format
            ),  # TODO: refactor date format
            "default_enabled": feature.default_enabled,
            "description": feature.description,
            "initial_value": feature.initial_value,
            "name": feature.name,
            "project": {
                "id": feature.project_id,
                "name": feature.project.name,
            },
            "type": feature.type,
        },
        "environment": {
            "id": environment.id,
            "name": environment.name,
        },
        "identity": identity_id,
        "identity_identifier": identity_identifier,
        "feature_segment": None,
    }

    previous_state = None
    if previous_enabled_state is not None and previous_value is not None:
        previous_state = default_data.update(
            enabled=previous_enabled_state, feature_state_value=previous_value
        )

    new_state = None
    if new_value is not None and previous_value is not None:
        new_state = default_data.update(
            enabled=new_enabled_state, feature_state_value=new_value
        )

    data = {
        "new_state": new_state,
        "changed_by": changed_by.email,
        "previous_state": previous_state,
    }

    event_type = (
        WebhookEventType.FLAG_DELETED
        if not new_state
        else WebhookEventType.FLAG_UPDATED
    )

    call_environment_webhooks(environment, data, event_type=event_type)
