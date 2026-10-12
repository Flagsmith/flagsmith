from features.future.mappers import map_flag_value
from features.future.types import (
    FlagValue,
    SegmentOverrideRequest,
    SegmentReference,
    Variant,
)
from features.models import FeatureStateValue
from features.types import LegacyFeatureStateData


def map_legacy_flag_value(
    feature_state_data: LegacyFeatureStateData,
) -> FlagValue | None:
    """Map the value of feature state data validated by a legacy API, if any.

    TODO: Remove after https://github.com/Flagsmith/flagsmith/issues/7641
    """
    if value_data := feature_state_data.get("feature_state_value"):
        return map_flag_value(FeatureStateValue(**value_data))
    return None


def clears_legacy_flag_value(feature_state_data: LegacyFeatureStateData) -> bool:
    """Whether feature state data validated by a legacy API clears the value.

    The flag API can't clear values, but the dashboard sends empty ones as null.

    TODO: Remove after https://github.com/Flagsmith/flagsmith/issues/7641
    """
    return bool(feature_state_data.get("feature_state_value")) and (
        map_legacy_flag_value(feature_state_data) is None
    )


def map_feature_state_data_to_segment_override(
    segment_id: int,
    feature_state_data: LegacyFeatureStateData,
    *,
    priority: int | None = None,
) -> SegmentOverrideRequest:
    """Map the feature state data validated by a legacy endpoint to an override.

    TODO: Remove after https://github.com/Flagsmith/flagsmith/issues/7641
    """
    override = SegmentOverrideRequest(segment=SegmentReference(id=segment_id))
    if priority is not None:
        override["priority"] = priority
    if "enabled" in feature_state_data:
        override["enabled"] = feature_state_data["enabled"]
    if value := map_legacy_flag_value(feature_state_data):
        override["value"] = value
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
