import logging

from django.core.exceptions import ObjectDoesNotExist
from simple_history.models import HistoricalRecords  # type: ignore[import-untyped]

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
    # Note: this task can run before the feature states of a newly created feature or
    # environment exist. `environments.tasks.process_environment_update` guards the
    # environment document write against that, using `Feature.is_creating` and
    # `Environment.is_creating`.
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
    )


def add_master_api_key(sender, **kwargs):  # type: ignore[no-untyped-def]
    try:
        history_instance = kwargs["history_instance"]
        master_api_key = HistoricalRecords.thread.request.user.key
        history_instance.master_api_key = master_api_key
    except (KeyError, AttributeError):
        pass
