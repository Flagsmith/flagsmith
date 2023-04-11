import logging
import typing

from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from environments.models import Environment, Webhook
from features.models import Feature, FeatureState
from task_processor.decorators import register_task_handler
from users.models import FFAdminUser
from webhooks.webhooks import WebhookEventType, call_environment_webhooks

logger = logging.getLogger(__name__)


@register_task_handler()
def call_environment_webhook_for_feature_state_change(
    feature_id: int,
    environment_api_key: str,
    identity_id: typing.Union[id, str],
    identity_identifier: str,
    changed_by_user_id: int,
    timestamp: str,
    new_enabled_state: bool = None,
    new_value: typing.Union[bool, int, str] = None,
    previous_enabled_state: bool = None,
    previous_value: typing.Union[bool, int, str] = None,
):
    environment = Environment.objects.get(api_key=environment_api_key)
    if not environment.webhooks.filter(enabled=True).exists():
        logger.debug(
            "No webhooks exist for environment %d. Not calling webhooks.",
            environment.id,
        )
        return

    feature = Feature.objects.get(id=feature_id)
    changed_by = FFAdminUser.objects.get(id=changed_by_user_id)

    data = {
        "changed_by": changed_by.email,
        "timestamp": timestamp,
        "new_state": None,
    }

    if previous_enabled_state is not None and previous_value is not None:
        data["previous_state"] = Webhook.generate_webhook_feature_state_data(
            feature=feature,
            environment=environment,
            identity_id=identity_id,
            identity_identifier=identity_identifier,
            enabled=previous_enabled_state,
            value=previous_value,
        )

    if new_enabled_state is not None and new_value is not None:
        data["new_state"] = Webhook.generate_webhook_feature_state_data(
            feature=feature,
            environment=environment,
            identity_id=identity_id,
            identity_identifier=identity_identifier,
            enabled=new_enabled_state,
            value=new_value,
        )

    event_type = (
        WebhookEventType.FLAG_DELETED
        if new_enabled_state is None
        else WebhookEventType.FLAG_UPDATED
    )

    call_environment_webhooks(environment, data, event_type=event_type)


@register_task_handler()
def sync_identity_document_features(identity_uuid: str):
    from .models import EdgeIdentity

    identity = EdgeIdentity.from_identity_document(
        EdgeIdentity.dynamo_wrapper.get_item_from_uuid(identity_uuid)
    )

    valid_feature_names = set(
        FeatureState.objects.filter(
            environment__api_key=identity.environment_api_key
        ).values_list("feature__name", flat=True)
    )

    identity.synchronise_features(valid_feature_names)
    EdgeIdentity.dynamo_wrapper.put_item(identity.to_document())


@register_task_handler()
def generate_audit_log_records(
    environment_api_key: str,
    identifier: str,
    identity_uuid: str,
    changes: dict,
    user_id: int = None,
    master_api_key_id: int = None,
):
    audit_records = []

    feature_override_changes = changes.get("feature_overrides")
    if not feature_override_changes:
        return

    environment = Environment.objects.select_related(
        "project", "project__organisation"
    ).get(api_key=environment_api_key)

    for feature_name, change_details in feature_override_changes.items():
        action = {"+": "created", "-": "deleted", "~": "updated"}.get(
            change_details.get("change_type")
        )
        log = f"Feature override {action} for feature '{feature_name}' and identity '{identifier}'"
        audit_records.append(
            AuditLog(
                project=environment.project,
                environment=environment,
                log=log,
                author_id=user_id,
                related_object_type=RelatedObjectType.EDGE_IDENTITY.name,
                related_object_uuid=identity_uuid,
                master_api_key_id=master_api_key_id,
            )
        )

    AuditLog.objects.bulk_create(audit_records)
