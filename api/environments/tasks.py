from datetime import timedelta

from django.db.models import Prefetch, Q
from django.utils import timezone
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
from features.multivariate.models import MultivariateFeatureStateValue
from features.versioning.models import EnvironmentFeatureVersion
from features.versioning.versioning_service import (
    get_environment_flags_list,
)
from sse import (  # type: ignore[attr-defined]
    send_environment_update_message_for_environment,
    send_environment_update_message_for_project,
)


@register_task_handler(priority=TaskPriority.HIGH)
def rebuild_environment_document(environment_id: int) -> None:
    Environment.write_environment_documents(environment_id=environment_id)


@register_task_handler(priority=TaskPriority.HIGHEST)
def process_environment_update(audit_log_id: int):  # type: ignore[no-untyped-def]
    audit_log = AuditLog.objects.get(id=audit_log_id)

    # Send environment document to dynamodb
    Environment.write_environment_documents(
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


@register_task_handler(timeout=timedelta(hours=1))
def clone_environment_feature_states(
    source_environment_id: int, clone_environment_id: int
) -> None:
    source = Environment.objects.get(id=source_environment_id)
    clone = Environment.objects.get(id=clone_environment_id)

    now = timezone.now()

    source_feature_states = get_environment_flags_list(
        environment=source,
        additional_prefetch_related_args=[
            Prefetch(
                "multivariate_feature_state_values",
                queryset=MultivariateFeatureStateValue.objects.select_related(
                    "multivariate_feature_option"
                ),
            )
        ],
        additional_filters=Q(identity__isnull=True),
    )

    # Since we only want to create a single version for each environment / feature
    # combination in the new environment to create a 'snapshot' of the source
    # environment, we keep a local cache of environment feature version objects
    # to avoid having to use get_or_create and hit the db unnecessarily.
    version_map: dict[int, EnvironmentFeatureVersion] = {}

    for feature_state in source_feature_states:
        kwargs = {"env": clone}

        if clone.use_v2_feature_versioning:
            if not (efv := version_map.get(feature_state.feature_id)):
                efv = EnvironmentFeatureVersion.create_initial_version(
                    environment=clone, feature=feature_state.feature
                )
                version_map[feature_state.feature_id] = efv

            kwargs.update(environment_feature_version=efv)
        else:
            kwargs.update(live_from=now)

        feature_state.clone(**kwargs)

    clone.is_creating = False
    clone.save()
