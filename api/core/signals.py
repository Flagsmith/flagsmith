from core.models import AbstractBaseAuditableModel

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
    #  - can we add this generically for all models that inherit from AbstractBaseAuditableModel?

    environment, project = instance.get_environment_and_project()
    log_message = {
        "+": instance.get_create_log_message,
        "-": instance.get_delete_log_message,
        "~": instance.get_update_log_message,
    }[history_instance.history_type]()
    audit_log = AuditLog.objects.create(
        history_record_id=history_instance.history_id,
        history_record_class_path=instance.history_record_class_path,
        environment=environment,
        project=project,
        author=history_user,
        related_object_id=instance.id,
        related_object_type=instance.related_object_type.name,
        log=log_message,
    )
    assert audit_log
