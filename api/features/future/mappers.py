"""https://docs.flagsmith.com/managing-flags/updating-flags"""

from features.feature_states.models import API_VALUE_TYPES
from features.future.types import (
    EnvironmentDefaultResponse,
    FlagValue,
    SegmentOverrideChanges,
    SegmentOverrideResponse,
    SegmentReference,
    Variant,
)
from features.models import FeatureState, FeatureStateValue
from features.types import LegacyFeatureStateData


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


def map_feature_state_data_to_segment_override(
    segment_id: int,
    feature_state_data: LegacyFeatureStateData,
    *,
    priority: int | None = None,
) -> SegmentOverrideChanges:
    """Map the feature state data validated by a legacy endpoint to an override.

    TODO: Remove after https://github.com/Flagsmith/flagsmith/issues/7641
    """
    override = SegmentOverrideChanges(segment=SegmentReference(id=segment_id))
    if priority is not None:
        override["priority"] = priority
    if "enabled" in feature_state_data:
        override["enabled"] = feature_state_data["enabled"]
    if value_data := feature_state_data.get("feature_state_value"):
        override["value"] = map_flag_value(FeatureStateValue(**value_data))
    if (
        multivariate_values := feature_state_data.get(
            "multivariate_feature_state_values"
        )
    ) is not None:
        override["variants"] = [
            Variant(
                id=value["multivariate_feature_option"].id,
                weight=value["percentage_allocation"],
            )
            for value in multivariate_values
        ]
    return override
