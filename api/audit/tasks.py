import typing

from django.contrib.auth import get_user_model

from audit.constants import FEATURE_STATE_WENT_LIVE_MESSAGE
from audit.models import AuditLog, RelatedObjectType
from features.models import FeatureSegment, FeatureState
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
        and not history_instance.diff_against(history_instance.prev_record).changes
    ):
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


@register_task_handler()
def create_segment_priorities_changed_audit_log(
    previous_id_priority_pairs: typing.List[typing.Tuple[int, int]],
    feature_segment_ids: typing.List[int],
    user_id: int = None,
    master_api_key_id: int = None,
):
    """
    This needs to be a separate task called by the view itself. This is because the OrderedModelBase class
    that the FeatureSegment model inherits from implicitly uses bulk update to move other feature segments
    out of the way.

    Given the implementation, it's not really possible (or perhaps desirable) to determine which moves
    were actually made by the user. The logic is such that it iterates over the list of priorities sent
    by the client. Take for example 2 overrides:

     segment_a - priority 0
     segment_b - priority 1

    A change to move segment_b to priority 0 will set the priority on segment_b to 0 (triggering a single
    write to the database). segment_a will be moved from 0 -> 1 using bulk update. This seems fine as we
    then know b was moved and don't really care that a was moved out of the way. If the user, however moves
    segment_a to priority 1, the single save will be done on segment_b since it'll be first in the list and
    segment_a will be bulk updated.

    This is a very simple case, and it likely gets more complicated / difficult to follow if there are more
    than 2 overrides.
    """

    # TODO: use previous priorities to show what changed.

    feature_segments = FeatureSegment.objects.filter(id__in=feature_segment_ids)
    if not feature_segments:
        return

    # all feature segments should have the same value for feature and environment
    environment = feature_segments[0].environment
    feature = feature_segments[0].feature

    AuditLog.objects.create(
        log=f"Segment overrides re-ordered for feature '{feature.name}'.",
        environment=environment,
        author_id=user_id,
        related_object_id=feature.id,
        related_object_type=RelatedObjectType.FEATURE.name,
        master_api_key_id=master_api_key_id,
    )
