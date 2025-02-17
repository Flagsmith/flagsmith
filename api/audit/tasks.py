import logging
import typing
from datetime import datetime

from django.contrib.auth import get_user_model
from django.utils import timezone
from task_processor.decorators import register_task_handler  # type: ignore[import-untyped]
from task_processor.models import TaskPriority  # type: ignore[import-untyped]

from audit.constants import (
    FEATURE_STATE_UPDATED_BY_CHANGE_REQUEST_MESSAGE,
    FEATURE_STATE_WENT_LIVE_MESSAGE,
)
from audit.models import AuditLog, RelatedObjectType  # type: ignore[attr-defined]

logger = logging.getLogger(__name__)


@register_task_handler(priority=TaskPriority.HIGHEST)  # type: ignore[misc]
def create_feature_state_went_live_audit_log(feature_state_id: int):  # type: ignore[no-untyped-def]
    _create_feature_state_audit_log_for_change_request(
        feature_state_id, FEATURE_STATE_WENT_LIVE_MESSAGE
    )


@register_task_handler(priority=TaskPriority.HIGHEST)  # type: ignore[misc]
def create_feature_state_updated_by_change_request_audit_log(feature_state_id: int):  # type: ignore[no-untyped-def]
    _create_feature_state_audit_log_for_change_request(
        feature_state_id, FEATURE_STATE_UPDATED_BY_CHANGE_REQUEST_MESSAGE
    )


def _create_feature_state_audit_log_for_change_request(  # type: ignore[no-untyped-def]
    feature_state_id: int, msg_template: str
):
    from features.models import FeatureState

    feature_state = FeatureState.objects.filter(id=feature_state_id).first()

    if not feature_state:
        logger.info(
            "FeatureState not found. Likely means the change request was deleted before scheduled_for."
        )
        return

    if not feature_state.change_request:
        raise RuntimeError("Feature state must have a change request")

    log = msg_template % (
        feature_state.feature.name,
        feature_state.change_request.title,
    )
    AuditLog.objects.create(
        related_object_id=feature_state.id,
        related_object_type=RelatedObjectType.FEATURE_STATE.name,
        environment=feature_state.environment,
        project=feature_state.environment.project,
        log=log,
        is_system_event=True,
        created_date=feature_state.live_from,
    )


@register_task_handler(priority=TaskPriority.HIGHEST)  # type: ignore[misc]
def create_audit_log_from_historical_record(  # type: ignore[no-untyped-def]
    history_instance_id: int,
    history_user_id: typing.Optional[int],
    history_record_class_path: str,
):
    model_class = AuditLog.get_history_record_model_class(history_record_class_path)
    history_instance = model_class.objects.get(history_id=history_instance_id)  # type: ignore[attr-defined]

    if (
        history_instance.history_type == "~"
        and history_instance.prev_record
        and not history_instance.diff_against(history_instance.prev_record).changes
    ):
        return

    user_model = get_user_model()

    instance = history_instance.instance
    if instance.get_skip_create_audit_log():
        return

    history_user = user_model.objects.filter(id=history_user_id).first()

    override_author = instance.get_audit_log_author(history_instance)
    if not (history_user or override_author or history_instance.master_api_key):
        return

    environment, project = instance.get_environment_and_project()

    related_object_id = instance.get_audit_log_related_object_id(history_instance)
    related_object_type = instance.get_audit_log_related_object_type(history_instance)

    if not related_object_id:
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
        history_record_class_path=history_record_class_path,
        environment=environment,
        project=project,
        author=override_author or history_user,
        related_object_id=related_object_id,
        related_object_type=related_object_type.name,
        log=log_message,
        master_api_key=history_instance.master_api_key,
        created_date=history_instance.history_date,
        **instance.get_extra_audit_log_kwargs(history_instance),
    )


@register_task_handler()  # type: ignore[misc]
def create_segment_priorities_changed_audit_log(  # type: ignore[no-untyped-def]
    previous_id_priority_pairs: typing.List[typing.Tuple[int, int]],
    feature_segment_ids: typing.List[int],
    user_id: int = None,  # type: ignore[assignment]
    master_api_key_id: int = None,  # type: ignore[assignment]
    changed_at: str = None,  # type: ignore[assignment]
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

    from features.models import FeatureSegment

    feature_segments = FeatureSegment.objects.filter(id__in=feature_segment_ids)
    if not feature_segments:
        return

    # all feature segments should have the same value for feature, environment and
    # environment feature version
    environment = feature_segments[0].environment
    feature = feature_segments[0].feature
    environment_feature_version_id = feature_segments[0].environment_feature_version_id

    if environment_feature_version_id is not None:
        # Don't create audit logs for FeatureSegments wrapped in a version
        # as this is handled by the feature history instead.
        return

    AuditLog.objects.create(
        log=f"Segment overrides re-ordered for feature '{feature.name}'.",
        environment=environment,
        project_id=environment.project_id,
        author_id=user_id,
        related_object_id=feature.id,
        related_object_type=RelatedObjectType.FEATURE.name,
        master_api_key_id=master_api_key_id,
        created_date=(
            datetime.fromisoformat(changed_at)
            if changed_at is not None
            else timezone.now()
        ),
    )
