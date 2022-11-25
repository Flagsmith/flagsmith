from core.models import AbstractBaseAuditableModel
from django.core.exceptions import ObjectDoesNotExist

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
    #  - handle master API keys

    override_author = instance.get_audit_log_author(history_instance)
    if not (history_user or override_author):
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

    if not log_message:
        return

    AuditLog.objects.create(
        history_record_id=history_instance.history_id,
        history_record_class_path=instance.history_record_class_path,
        environment_id=getattr(environment, "id", None),
        project_id=getattr(project, "id", None),
        author=override_author or history_user,
        related_object_id=instance.id,
        related_object_type=instance.related_object_type.name,
        log=log_message,
        **instance.get_extra_audit_log_kwargs(history_instance),
    )
