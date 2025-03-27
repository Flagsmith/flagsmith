import logging

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from simple_history.models import HistoricalRecords  # type: ignore[import-untyped]
from task_processor.task_run_method import TaskRunMethod

from audit import tasks
from core.models import AbstractBaseAuditableModel
from users.models import FFAdminUser

logger = logging.getLogger(__name__)


def create_audit_log_from_historical_record(  # type: ignore[no-untyped-def]
    instance: AbstractBaseAuditableModel,
    history_user: FFAdminUser,
    history_instance,
    **kwargs,
):
    # The environment document in dynamodb is updated based on the post_save signal from the audit log
    # When creating a new feature, the feature states are created after the feature has been created.
    # i.e: the below task gets created/scheduled before feature states are created
    # Usually, there is enough time for the main thread to create the feature states
    # before the task is executed, but not always.
    # In those cases, we send the environment document to dynamodb without any feature states for the new feature.
    # In order to avoid this, either we need to update environment
    # document when creating feature states
    # or delay the execution of this task
    # We prefer to delay the execution of the task because of it's low surface area
    delay_until = (
        timezone.now() + timezone.timedelta(seconds=1)  # type: ignore[attr-defined]
        if settings.TASK_RUN_METHOD == TaskRunMethod.TASK_PROCESSOR
        else None
    )
    if instance.get_skip_create_audit_log():
        return

    try:
        environment, project = instance.get_environment_and_project()
    except ObjectDoesNotExist:
        logger.warning(
            "Unable to create audit log for %s %s. "
            "Parent model does not exist - this likely means it was hard deleted.",
            instance.related_object_type,
            getattr(instance, "id", "uuid"),
            exc_info=True,
        )
        return

    if project != history_instance.instance and (
        (project and project.deleted_at)
        or (environment and environment.project.deleted_at)
    ):
        # don't trigger audit log records in deleted projects
        return

    tasks.create_audit_log_from_historical_record.delay(
        kwargs={
            "history_instance_id": history_instance.history_id,
            "history_user_id": getattr(history_user, "id", None),
            "history_record_class_path": instance.history_record_class_path,
        },
        delay_until=delay_until,
    )


def add_master_api_key(sender, **kwargs):  # type: ignore[no-untyped-def]
    try:
        history_instance = kwargs["history_instance"]
        master_api_key = HistoricalRecords.thread.request.user.key
        history_instance.master_api_key = master_api_key
    except (KeyError, AttributeError):
        pass
