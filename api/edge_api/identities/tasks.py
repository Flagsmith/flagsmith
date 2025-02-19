import logging
import typing

from django.utils import timezone
from task_processor.decorators import register_task_handler  # type: ignore[import-untyped]
from task_processor.models import TaskPriority  # type: ignore[import-untyped]

from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from edge_api.identities.types import IdentityChangeset
from environments.dynamodb import DynamoEnvironmentV2Wrapper
from environments.models import Environment, Webhook
from features.models import Feature, FeatureState
from users.models import FFAdminUser
from util.mappers import map_identity_changeset_to_identity_override_changeset
from webhooks.webhooks import WebhookEventType, call_environment_webhooks

logger = logging.getLogger(__name__)


@register_task_handler()  # type: ignore[misc]
def call_environment_webhook_for_feature_state_change(  # type: ignore[no-untyped-def]
    feature_id: int,
    environment_api_key: str,
    identity_id: typing.Union[id, str],  # type: ignore[valid-type]
    identity_identifier: str,
    timestamp: str,
    changed_by_user_id: int = None,  # type: ignore[assignment] # deprecated(use changed_by)
    changed_by: str = None,  # type: ignore[assignment]
    new_enabled_state: bool = None,  # type: ignore[assignment]
    new_value: typing.Union[bool, int, str] = None,  # type: ignore[assignment]
    previous_enabled_state: bool = None,  # type: ignore[assignment]
    previous_value: typing.Union[bool, int, str] = None,  # type: ignore[assignment]
):
    environment = Environment.objects.get(api_key=environment_api_key)
    if not environment.webhooks.filter(enabled=True).exists():
        logger.debug(
            "No webhooks exist for environment %d. Not calling webhooks.",
            environment.id,
        )
        return

    feature = Feature.objects.get(id=feature_id)
    if changed_by_user_id:
        changed_by = FFAdminUser.objects.get(id=changed_by_user_id).email

    data = {
        "changed_by": changed_by,
        "timestamp": timestamp,
        "new_state": None,
    }

    if previous_enabled_state is not None:
        data["previous_state"] = Webhook.generate_webhook_feature_state_data(  # type: ignore[assignment]
            feature=feature,
            environment=environment,
            identity_id=identity_id,
            identity_identifier=identity_identifier,
            enabled=previous_enabled_state,
            value=previous_value,
        )

    if new_enabled_state is not None:
        data["new_state"] = Webhook.generate_webhook_feature_state_data(  # type: ignore[assignment]
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

    call_environment_webhooks(environment.id, data, event_type=event_type.value)


@register_task_handler(priority=TaskPriority.HIGH)  # type: ignore[misc]
def sync_identity_document_features(identity_uuid: str):  # type: ignore[no-untyped-def]
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
    identity.save()


@register_task_handler()  # type: ignore[misc]
def generate_audit_log_records(
    environment_api_key: str,
    identifier: str,
    identity_uuid: str,
    changes: IdentityChangeset,
    user_id: int | None = None,
    master_api_key_id: int | None = None,
) -> None:
    audit_records = []

    feature_override_changes = changes["feature_overrides"]
    if not feature_override_changes:
        return

    environment = Environment.objects.select_related(
        "project", "project__organisation"
    ).get(api_key=environment_api_key)

    for feature_name, change_details in feature_override_changes.items():
        action = {"+": "created", "-": "deleted", "~": "updated"}.get(
            change_details["change_type"]
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
                created_date=timezone.now(),
            )
        )

    AuditLog.objects.bulk_create(audit_records)


@register_task_handler()  # type: ignore[misc]
def update_flagsmith_environments_v2_identity_overrides(
    environment_api_key: str,
    identity_uuid: str,
    identifier: str,
    changes: IdentityChangeset,
) -> None:
    feature_override_changes = changes["feature_overrides"]
    if not feature_override_changes:
        return

    environment = Environment.objects.get(api_key=environment_api_key)
    dynamodb_wrapper_v2 = DynamoEnvironmentV2Wrapper()

    identity_override_changeset = map_identity_changeset_to_identity_override_changeset(
        identity_changeset=changes,
        identity_uuid=identity_uuid,
        environment_api_key=environment_api_key,
        environment_id=environment.id,
        identifier=identifier,
    )
    dynamodb_wrapper_v2.update_identity_overrides(identity_override_changeset)


@register_task_handler()  # type: ignore[misc]
def delete_environments_v2_identity_overrides_by_feature(feature_id: int) -> None:
    dynamodb_wrapper_v2 = DynamoEnvironmentV2Wrapper()

    feature = Feature.objects.all_with_deleted().get(id=feature_id)
    for environment in feature.project.environments.all():
        dynamodb_wrapper_v2.delete_identity_overrides(
            environment_id=environment.id, feature_id=feature_id
        )
