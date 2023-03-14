from audit.constants import FEATURE_STATE_WENT_LIVE_MESSAGE
from audit.models import AuditLog
from audit.tasks import create_feature_state_went_live_audit_log


def test_create_feature_state_went_live_audit_log(change_request_feature_state):
    # Given
    message = FEATURE_STATE_WENT_LIVE_MESSAGE % (
        change_request_feature_state.feature.name,
        change_request_feature_state.change_request.title,
    )
    feature_state_id = change_request_feature_state.id

    # When
    create_feature_state_went_live_audit_log(feature_state_id)

    # Then
    assert (
        AuditLog.objects.filter(
            related_object_id=feature_state_id, is_system_event=True, log=message
        ).count()
        == 1
    )


def test_create_feature_state_wen_live_audit_log_does_nothing_if_feature_state_deleted(
    change_request_feature_state,
):
    # Given
    message = FEATURE_STATE_WENT_LIVE_MESSAGE % (
        change_request_feature_state.feature.name,
        change_request_feature_state.change_request.title,
    )
    change_request_feature_state.delete()
    feature_state_id = change_request_feature_state.id

    # When
    create_feature_state_went_live_audit_log(feature_state_id)

    # Then
    assert (
        AuditLog.objects.filter(
            related_object_id=feature_state_id, is_system_event=True, log=message
        ).count()
        == 0
    )
