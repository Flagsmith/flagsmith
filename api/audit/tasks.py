import typing

from django.contrib.auth import get_user_model

from audit.constants import FEATURE_STATE_WENT_LIVE_MESSAGE
from audit.models import AuditLog, RelatedObjectType
from features.models import FeatureState
from task_processor.decorators import register_task_handler

user_model = get_user_model()


@register_task_handler()
def create_feature_state_went_live_audit_log(feature_state_id: int):
    feature_state = FeatureState.objects.get(id=feature_state_id)

    if not feature_state.change_request:
        raise RuntimeError("Feature state must have a change request")

    message = FEATURE_STATE_WENT_LIVE_MESSAGE % (
        feature_state.feature.name,
        feature_state.change_request.title,
    )
    AuditLog.objects.create(
        related_object_id=feature_state.id,
        related_object_type=RelatedObjectType.FEATURE_STATE.name,
        environment=feature_state.environment,
        project=feature_state.environment.project,
        log=message,
        is_system_event=True,
    )


@register_task_handler()
def create_audit_log_from_historical_record(
    history_instance_id: int,
    history_user_id: typing.Optional[int],
    history_record_class_path: str,
):
    model_class = AuditLog.get_history_record_model_class(history_record_class_path)
    history_instance = model_class.objects.get(history_id=history_instance_id)

    if (
        history_instance.history_type == "~"
        and history_instance.diff_against(history_instance.prev_record).changes == []
    ):
        # don't write audit log if no changes
        return

    instance = history_instance.instance
    history_user = user_model.objects.filter(id=history_user_id).first()

    override_author = instance.get_audit_log_author(history_instance)
    if not (history_user or override_author or history_instance.master_api_key):
        return

    environment, project = instance.get_environment_and_project()

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
        history_record_class_path=history_record_class_path,
        environment=environment,
        project=project,
        author=override_author or history_user,
        related_object_id=related_object_id,
        related_object_type=related_object_type.name,
        log=log_message,
        master_api_key=history_instance.master_api_key,
        **instance.get_extra_audit_log_kwargs(history_instance),
    )
