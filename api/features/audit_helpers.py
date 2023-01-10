import typing_extensions

from audit.constants import (
    DATETIME_FORMAT,
    FEATURE_CREATED_MESSAGE,
    FEATURE_STATE_SCHEDULED_MESSAGE,
    IDENTITY_FEATURE_STATE_SCHEDULED_MESSAGE,
    IDENTITY_FEATURE_STATE_UPDATED_MESSAGE,
    SEGMENT_FEATURE_STATE_SCHEDULED_MESSAGE,
    SEGMENT_FEATURE_STATE_UPDATED_MESSAGE,
)

if typing_extensions.TYPE_CHECKING:
    from .models import FeatureState


def get_identity_override_created_audit_message(feature_state: "FeatureState") -> str:
    base_message = (
        IDENTITY_FEATURE_STATE_SCHEDULED_MESSAGE
        if feature_state.is_scheduled
        else IDENTITY_FEATURE_STATE_UPDATED_MESSAGE
    )
    args = (
        feature_state.feature.name,
        feature_state.identity.identifier,
    )
    if feature_state.is_scheduled:
        args = (feature_state.live_from.strftime(DATETIME_FORMAT), *args)
    return base_message % args


def get_segment_override_created_audit_message(feature_state: "FeatureState") -> str:
    base_message = (
        SEGMENT_FEATURE_STATE_SCHEDULED_MESSAGE
        if feature_state.is_scheduled
        else SEGMENT_FEATURE_STATE_UPDATED_MESSAGE
    )
    args = (feature_state.feature.name, feature_state.feature_segment.segment.name)
    if feature_state.is_scheduled:
        args = (feature_state.live_from.strftime(DATETIME_FORMAT), *args)
    return base_message % args


def get_environment_feature_state_created_audit_message(
    feature_state: "FeatureState",
) -> str:
    base_message = (
        FEATURE_STATE_SCHEDULED_MESSAGE
        if feature_state.is_scheduled
        else FEATURE_CREATED_MESSAGE
    )
    args = (feature_state.feature.name,)
    if feature_state.is_scheduled:
        args = (feature_state.live_from.strftime(DATETIME_FORMAT), *args)
    return base_message % args
