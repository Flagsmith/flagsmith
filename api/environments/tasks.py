from task_processor.decorators import (
    register_task_handler,
)
from task_processor.models import TaskPriority

from audit.models import AuditLog
from environments.dynamodb import DynamoIdentityWrapper
from environments.models import (
    Environment,
    environment_v2_wrapper,
    environment_wrapper,
)
from features.versioning.models import EnvironmentFeatureVersion
from sse import (  # type: ignore[attr-defined]
    send_environment_update_message_for_environment,
    send_environment_update_message_for_project,
)


@register_task_handler(priority=TaskPriority.HIGH)
def rebuild_environment_document(environment_id: int) -> None:
    Environment.write_environments_to_dynamodb(environment_id=environment_id)


@register_task_handler(priority=TaskPriority.HIGHEST)
def process_environment_update(audit_log_id: int):  # type: ignore[no-untyped-def]
    audit_log = AuditLog.objects.get(id=audit_log_id)

    # Send environment document to dynamodb
    Environment.write_environments_to_dynamodb(
        environment_id=audit_log.environment_id, project_id=audit_log.project_id
    )

    # send environment update message
    if audit_log.environment_id:
        send_environment_update_message_for_environment(audit_log.environment)
    else:
        send_environment_update_message_for_project(audit_log.project)


@register_task_handler()
def delete_environment_from_dynamo(api_key: str, environment_id: str):  # type: ignore[no-untyped-def]
    # Delete environment
    environment_wrapper.delete_environment(api_key)

    # Delete identities
    identity_wrapper = DynamoIdentityWrapper()
    identity_wrapper.delete_all_identities(api_key)

    # Delete environment_v2 documents
    environment_v2_wrapper.delete_environment(environment_id)  # type: ignore[arg-type]


@register_task_handler()
def delete_environment(environment_id: int) -> None:
    Environment.objects.get(id=environment_id).delete()


@register_task_handler()
def clone_environment_feature_states(
    source_environment_id: int, clone_environment_id: int
) -> None:
    source = Environment.objects.get(id=source_environment_id)
    clone = Environment.objects.get(id=clone_environment_id)

    # Since identities are closely tied to the environment
    # it does not make much sense to clone them, hence
    # only clone feature states without identities
    queryset = source.feature_states.filter(identity=None)

    if source.use_v2_feature_versioning:
        # Grab the latest feature versions from the source environment.
        latest_environment_feature_versions = (
            EnvironmentFeatureVersion.objects.get_latest_versions_as_queryset(
                environment_id=source.id
            )
        )

        # Create a dictionary holding the environment feature versions (unique per feature)
        # to use in the cloned environment.
        clone_environment_feature_versions = {
            efv.feature_id: efv.clone_to_environment(environment=clone)
            for efv in latest_environment_feature_versions
        }

        for feature_state in queryset.filter(
            environment_feature_version__in=latest_environment_feature_versions
        ):
            clone_efv = clone_environment_feature_versions[feature_state.feature_id]
            feature_state.clone(clone, environment_feature_version=clone_efv)
    else:
        for feature_state in queryset:
            feature_state.clone(clone, live_from=feature_state.live_from)

    clone.is_creating = False
    clone.save()
