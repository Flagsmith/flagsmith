from datetime import timedelta

import structlog
from django.conf import settings
from django.db.models import Prefetch, Q
from django.utils import timezone
from task_processor.decorators import (
    register_task_handler,
)
from task_processor.models import TaskPriority
from task_processor.task_run_method import TaskRunMethod

from audit.models import AuditLog
from environments.constants import (
    ENVIRONMENT_DOCUMENT_WRITE_DEFERRAL_SECONDS,
    ENVIRONMENT_DOCUMENT_WRITE_MAX_DEFERRALS,
)
from environments.dynamodb import DynamoIdentityWrapper
from environments.models import (
    Environment,
    environment_v2_wrapper,
    environment_wrapper,
)
from features.models import Feature
from features.multivariate.models import MultivariateFeatureStateValue
from features.versioning.models import EnvironmentFeatureVersion
from features.versioning.versioning_service import (
    get_environment_flags_list,
)
from sse import (  # type: ignore[attr-defined]
    send_environment_update_message_for_environment,
    send_environment_update_message_for_project,
)

logger = structlog.get_logger("environments")


@register_task_handler(priority=TaskPriority.HIGH)
def rebuild_environment_document(environment_id: int) -> None:
    Environment.write_environment_documents(environment_id=environment_id)


def _is_seeding_feature_states(audit_log: AuditLog) -> bool:
    """
    Whether any environment or feature the audit log covers is still seeding its
    initial feature states, and would therefore be written to DynamoDB incomplete.
    """
    environments_filter = Q(project_id=audit_log.project_id)
    if audit_log.environment_id:
        environments_filter &= Q(id=audit_log.environment_id)

    return bool(
        Environment.objects.filter(environments_filter, is_creating=True).exists()
        or Feature.objects.filter(
            project_id=audit_log.project_id, is_creating=True
        ).exists()
    )


@register_task_handler(priority=TaskPriority.HIGHEST)
def process_environment_update(audit_log_id: int, deferrals: int = 0):  # type: ignore[no-untyped-def]
    audit_log = AuditLog.objects.get(id=audit_log_id)

    # Deferring relies on `delay_until`, which is a no-op without the task processor —
    # re-enqueueing there would drop the write and leave the document stale.
    if (
        settings.TASK_RUN_METHOD == TaskRunMethod.TASK_PROCESSOR
        and _is_seeding_feature_states(audit_log)
    ):
        if deferrals < ENVIRONMENT_DOCUMENT_WRITE_MAX_DEFERRALS:
            process_environment_update.delay(
                kwargs={"audit_log_id": audit_log_id, "deferrals": deferrals + 1},
                delay_until=timezone.now()
                + timedelta(
                    seconds=ENVIRONMENT_DOCUMENT_WRITE_DEFERRAL_SECONDS * 2**deferrals
                ),
            )
            return

        # Writing a document that may be missing feature states is preferable to not
        # writing one at all, since a stuck `is_creating` flag would otherwise stop
        # every future update to this environment.
        logger.warning(
            "environment_document.written_while_seeding",
            audit_log__id=audit_log_id,
            environment__id=audit_log.environment_id,
            project__id=audit_log.project_id,
        )

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


@register_task_handler()
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

    # Since, in versioned environments, we only want to create a single version for
    # each feature to create a 'snapshot' of the source environment, we keep a local
    # cache of EnvironmentFeatureVersion objects to avoid having to use get_or_create
    # and hit the db unnecessarily.
    efv_by_feature_id: dict[int, EnvironmentFeatureVersion] = {}

    for feature_state in source_feature_states:
        kwargs = {"env": clone}

        if clone.use_v2_feature_versioning:
            if not (efv := efv_by_feature_id.get(feature_state.feature_id)):
                efv = EnvironmentFeatureVersion.create_initial_version(
                    environment=clone, feature=feature_state.feature
                )
                efv_by_feature_id[feature_state.feature_id] = efv

            kwargs.update(environment_feature_version=efv)
        else:
            kwargs.update(live_from=now)

        feature_state.clone(**kwargs)

    clone.is_creating = False
    clone.save()
