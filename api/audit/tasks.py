from audit.models import (
    FEATURE_STATE_WENT_LIVE_MESSAGE,
    AuditLog,
    RelatedObjectType,
)
from features.models import FeatureState
from task_processor.decorators import register_task_handler


@register_task_handler()
def create_feature_state_went_live_audit_log(feature_state_id: int):
    feature_state = FeatureState.objects.get(id=feature_state_id)
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
