from audit.models import FEATURE_STATE_WENT_LIVE_MESSAGE, AuditLog
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
    AuditLog.objects.get(
        related_object_id=feature_state_id, is_system_event=True, log=message
    )
