from features.future.mappers import map_flag_value
from features.future.types import (
    FlagValue,
    SegmentOverrideRequest,
    SegmentReference,
    Variant,
)
from features.models import Feature, FeatureStateValue
from features.types import LegacyFeatureStateData


def map_legacy_flag_value(
    feature_state_data: LegacyFeatureStateData,
) -> FlagValue | None:
    """Map a legacy feature state value to the flag API representation.

    TODO: Remove after https://github.com/Flagsmith/flagsmith/issues/1667
    """
    if value_data := feature_state_data.get("feature_state_value"):
        return map_flag_value(FeatureStateValue(**value_data))
    return None


def clears_legacy_flag_value(feature_state_data: LegacyFeatureStateData) -> bool:
    """Whether a legacy payload explicitly sets the feature value to null.

    Omitting feature_state_value leaves the existing value unchanged, while
    providing a typed null value clears it.

    TODO: Remove after https://github.com/Flagsmith/flagsmith/issues/1667
    """
    return bool(feature_state_data.get("feature_state_value")) and (
        map_legacy_flag_value(feature_state_data) is None
    )


def map_feature_state_data_to_segment_override(
    feature: Feature,
    segment_id: int,
    feature_state_data: LegacyFeatureStateData,
    *,
    priority: int | None = None,
) -> SegmentOverrideRequest:
    """Map the feature state data validated by a legacy endpoint to an override.

    Legacy endpoints remove variants left out, so they're weighted 0.

    TODO: Remove after https://github.com/Flagsmith/flagsmith/issues/1667
    """
    override = SegmentOverrideRequest(segment=SegmentReference(id=segment_id))
    if priority is not None:
        override["priority"] = priority
    if "enabled" in feature_state_data:
        override["enabled"] = feature_state_data["enabled"]
    if clears_legacy_flag_value(feature_state_data):
        override["value"] = None
    elif value := map_legacy_flag_value(feature_state_data):
        override["value"] = value
    if (
        multivariate_values := feature_state_data.get(
            "multivariate_feature_state_values"
        )
    ) is not None:
        variants = [
            Variant(
                id=value["multivariate_feature_option"].id,
                weight=value["percentage_allocation"],
            )
            for value in multivariate_values
        ]
        given_ids = {variant["id"] for variant in variants}
        variants += [
            Variant(id=variant_id, weight=0)
            for variant_id in feature.multivariate_options.values_list("id", flat=True)
            if variant_id not in given_ids
        ]
        if variants:  # Legacy clients may send an empty list for standard features.
            override["variants"] = variants
    return override
