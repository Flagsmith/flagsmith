from core.models import AbstractBaseAuditableModel
from django.core.exceptions import ObjectDoesNotExist
from simple_history.models import HistoricalRecords

from audit.models import AuditLog
from users.models import FFAdminUser


def create_audit_log_from_historical_record(
    instance: AbstractBaseAuditableModel,
    history_user: FFAdminUser,
    history_instance,  # TODO: typing
    **kwargs,
):
    # TODO:
    #  - This should be done in a task

    override_author = instance.get_audit_log_author(history_instance)
    if not (history_user or override_author or history_instance.master_api_key):
        return

    try:
        environment, project = instance.get_environment_and_project()
    except ObjectDoesNotExist:
        # This can occur in cases of cascade deletes
        return

    log_message = {
        "+": instance.get_create_log_message,
        "-": instance.get_delete_log_message,
        "~": instance.get_update_log_message,
    }[history_instance.history_type](history_instance)

    related_object_id = instance.get_audit_log_related_object_id(history_instance)
    related_object_type = instance.get_audit_log_related_object_type(history_instance)

    if not (log_message and related_object_id):
        return

    AuditLog.objects.create(
        history_record_id=history_instance.history_id,
        history_record_class_path=instance.history_record_class_path,
        environment_id=getattr(environment, "id", None),
        project_id=getattr(project, "id", None),
        author=override_author or history_user,
        related_object_id=related_object_id,
        related_object_type=related_object_type.name,
        log=log_message,
        master_api_key=history_instance.master_api_key,
        **instance.get_extra_audit_log_kwargs(history_instance),
    )


def add_master_api_key(sender, **kwargs):
    try:
        history_instance = kwargs["history_instance"]
        history_instance.master_api_key = (
            HistoricalRecords.thread.request.master_api_key
        )
    except (KeyError, AttributeError):
        pass
