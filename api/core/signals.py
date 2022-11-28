from core.models import AbstractBaseAuditableModel
from simple_history.models import HistoricalRecords

from audit import tasks
from users.models import FFAdminUser


def create_audit_log_from_historical_record(
    instance: AbstractBaseAuditableModel,
    history_user: FFAdminUser,
    history_instance,  # TODO: typing
    **kwargs,
):
    tasks.create_audit_log_from_historical_record.delay(
        kwargs={
            "history_instance_id": history_instance.history_id,
            "history_user_id": getattr(history_user, "id", None),
            "history_record_class_path": instance.history_record_class_path,
        }
    )


def add_master_api_key(sender, **kwargs):
    try:
        history_instance = kwargs["history_instance"]
        history_instance.master_api_key = (
            HistoricalRecords.thread.request.master_api_key
        )
    except (KeyError, AttributeError):
        pass
