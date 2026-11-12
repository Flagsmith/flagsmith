"""https://docs.flagsmith.com/managing-flags/updating-flags"""

from features.feature_states.models import API_VALUE_TYPES
from features.future.types import (
    EnvironmentDefaultResponse,
    FlagValue,
    SegmentOverrideResponse,
    SegmentReference,
    Variant,
)
from features.models import FeatureState, FeatureStateValue


def map_flag_value(feature_state_value: FeatureStateValue) -> FlagValue | None:
    """Render a stored value as a typed value object, always with a string value."""
    value = feature_state_value.value
    if value is None:
        return None
    return FlagValue(
        type=API_VALUE_TYPES.get(feature_state_value.type, "string"),  # type: ignore[arg-type]
        value=("true" if value else "false") if isinstance(value, bool) else str(value),
    )


def map_variants(feature_state: FeatureState) -> list[Variant]:
    """List a feature state's variant weights, ordered by variant."""
    return [
        Variant(
            id=multivariate_value.multivariate_feature_option_id,
            weight=multivariate_value.percentage_allocation,
        )
        for multivariate_value in sorted(
            feature_state.multivariate_feature_state_values.all(),
            key=lambda multivariate_value: (
                multivariate_value.multivariate_feature_option_id
            ),
        )
    ]


def map_environment_default(feature_state: FeatureState) -> EnvironmentDefaultResponse:
    """Render a feature state as the flag's default for its environment."""
    return EnvironmentDefaultResponse(
        enabled=feature_state.enabled,
        value=map_flag_value(feature_state.feature_state_value),
        variants=map_variants(feature_state),
    )


def map_segment_override(
    feature_state: FeatureState,
) -> SegmentOverrideResponse | None:
    """Render a feature state as one of the flag's segment overrides."""
    feature_segment = feature_state.feature_segment
    if feature_segment is None:
        return None
    return SegmentOverrideResponse(
        segment=SegmentReference(id=feature_segment.segment_id),
        priority=feature_segment.priority,
        enabled=feature_state.enabled,
        value=map_flag_value(feature_state.feature_state_value),
        variants=map_variants(feature_state),
    )
