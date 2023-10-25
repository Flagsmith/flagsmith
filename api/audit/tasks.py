import logging
import typing

from core.models import _AbstractBaseAuditableModel
from django.contrib.auth import get_user_model

from audit.constants import (
    FEATURE_STATE_UPDATED_BY_CHANGE_REQUEST_MESSAGE,
    FEATURE_STATE_WENT_LIVE_MESSAGE,
)
from audit.models import AuditLog, RelatedObjectType
from task_processor.decorators import register_task_handler

logger = logging.getLogger(__name__)


@register_task_handler()
def create_feature_state_went_live_audit_log(feature_state_id: int):
    _create_feature_state_audit_log_for_change_request(
        feature_state_id, FEATURE_STATE_WENT_LIVE_MESSAGE
    )


@register_task_handler()
def create_feature_state_updated_by_change_request_audit_log(feature_state_id: int):
    _create_feature_state_audit_log_for_change_request(
        feature_state_id, FEATURE_STATE_UPDATED_BY_CHANGE_REQUEST_MESSAGE
    )


def _create_feature_state_audit_log_for_change_request(
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
        environment=feature_state._get_environment(),
        project=feature_state._get_project(),
        log=log,
        related_object_id=feature_state.pk,
        related_object_type=RelatedObjectType.FEATURE_STATE.name,
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
        and history_instance.prev_record
        and not history_instance.diff_against(history_instance.prev_record).changes
    ):
        # no auditable data changed in this change/event
        return

    instance: _AbstractBaseAuditableModel = history_instance.instance

    history_user = get_user_model().objects.filter(id=history_user_id).first()
    override_author = instance.get_audit_log_author(history_instance)
    if not (history_user or override_author or history_instance.master_api_key):
        # no known author for this change/event
        return

    (
        organisations,
        project,
        environment,
    ) = instance.get_organisations_project_environment()

    related_object_id = instance.get_audit_log_related_object_id(history_instance)
    related_object_type = instance.get_audit_log_related_object_type(history_instance)
    if not related_object_id:
        # no related object for this change/event
        return

    log_message = {
        "+": instance.get_create_log_message,
        "-": instance.get_delete_log_message,
        "~": instance.get_update_log_message,
    }[history_instance.history_type](history_instance)
    if not log_message:
        # no log to record for this change/event
        return

    audit_logs = [
        AuditLog(
            organisation=organisation,
            environment=environment,
            project=project,
            author=override_author or history_user,
            related_object_id=related_object_id,
            related_object_type=related_object_type.name,
            log=log_message,
            history_record_id=history_instance.history_id,
            history_record_class_path=history_record_class_path,
            master_api_key=history_instance.master_api_key,
            **instance.get_extra_audit_log_kwargs(history_instance),
        )
        for organisation in organisations
    ]
    AuditLog.objects.bulk_create(audit_logs)


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

    from features.models import FeatureSegment

    feature_segments = FeatureSegment.objects.filter(id__in=feature_segment_ids)
    if not feature_segments:
        return

    # all feature segments should have the same value for environment and feature
    feature_segment = feature_segments[0]
    environment = feature_segment._get_environment()
    feature = feature_segment.feature

    AuditLog.objects.create(
        environment=environment,
        log=f"Segment overrides re-ordered for feature '{feature.name}'.",
        author_id=user_id,
        master_api_key_id=master_api_key_id,
        related_object_id=feature.pk,
        related_object_type=RelatedObjectType.FEATURE.name,
    )


@register_task_handler()
def create_audit_log_user_logged_in(user_id: int):
    if not (user := get_user_model().objects.filter(id=user_id).first()):
        logger.warning(
            f"User with id {user_id} not found. Audit log for user logged in not created."
        )
        return

    user = typing.cast(_AbstractBaseAuditableModel, user)
    log_message = (
        f"{RelatedObjectType.USER.value} logged in: {user.get_audit_log_identity()}"
    )

    audit_logs = [
        AuditLog(
            organisation=organisation,
            related_object_id=user.pk,
            related_object_type=RelatedObjectType.USER.name,
            log=log_message,
            is_system_event=True,
        )
        for organisation in user._get_organisations()
    ]
    AuditLog.objects.bulk_create(audit_logs)


@register_task_handler()
def create_audit_log_user_logged_out(user_id: int):
    if not (user := get_user_model().objects.filter(id=user_id).first()):
        logger.warning(
            f"User with id {user_id} not found. Audit log for user logged out not created."
        )
        return

    user = typing.cast(_AbstractBaseAuditableModel, user)
    log_message = (
        f"{RelatedObjectType.USER.value} logged out: {user.get_audit_log_identity()}"
    )

    audit_logs = [
        AuditLog(
            organisation=organisation,
            related_object_id=user.pk,
            related_object_type=RelatedObjectType.USER.name,
            log=log_message,
            is_system_event=True,
        )
        for organisation in user._get_organisations()
    ]
    AuditLog.objects.bulk_create(audit_logs)


@register_task_handler()
def create_audit_log_user_login_failed(
    credentials: dict, codes: list[str] | str | None = None
):
    if not (username := credentials.get("username")):
        return
    # ModelBackend looks up user this way, so we will do the same
    if not (user := get_user_model()._default_manager.get_by_natural_key(username)):
        return
    if not isinstance(user, _AbstractBaseAuditableModel):
        return

    codes = [codes] if type(codes) is str else codes
    reason = ",".join(codes) if codes else "password"
    log_message = f"{RelatedObjectType.USER.value} login failed ({reason}): {user.get_audit_log_identity()}"

    audit_logs = [
        AuditLog(
            organisation=organisation,
            related_object_id=user.pk,
            related_object_type=RelatedObjectType.USER.name,
            log=log_message,
            is_system_event=True,
        )
        for organisation in user._get_organisations()
    ]
    AuditLog.objects.bulk_create(audit_logs)
