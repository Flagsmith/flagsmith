from django.db import transaction
from django.db.models import Max, Q
from django.utils import timezone

from core.dataclasses import AuthorData
from environments.models import Environment
from features.feature_segments.mappers import (
    clears_legacy_flag_value,
    map_feature_state_data_to_segment_override,
)
from features.future.mappers import map_flag_value
from features.future.services import update_flag
from features.models import Feature, FeatureSegment, FeatureState
from features.types import LegacyFeatureStateData
from features.versioning.versioning_service import (
    get_current_live_environment_feature_version,
    get_environment_flags_list,
)
from integrations.vcs.services import dispatch_vcs_on_feature_state_changed


def get_segment_override(
    *, environment: Environment, feature: Feature, segment_id: int
) -> FeatureState | None:
    """Get the flag's live override for a segment, if any.

    TODO: Remove after https://github.com/Flagsmith/flagsmith/issues/7641
    """
    overrides = get_environment_flags_list(
        environment,
        additional_filters=Q(
            feature_id=feature.id,
            feature_segment__segment_id=segment_id,
            identity__isnull=True,
        ),
        additional_prefetch_related_args=["multivariate_feature_state_values"],
    )
    return overrides[0] if overrides else None


def is_live_segment_override(feature_segment: FeatureSegment) -> bool:
    """Whether a feature segment is the one the flag serves its segment override from.

    TODO: Remove after https://github.com/Flagsmith/flagsmith/issues/7641
    """
    override = get_segment_override(
        environment=feature_segment.environment,
        feature=feature_segment.feature,
        segment_id=feature_segment.segment_id,
    )
    return override is not None and override.feature_segment_id == feature_segment.id


def get_next_segment_override_priority(
    *, environment: Environment, feature: Feature
) -> int:
    version = (
        get_current_live_environment_feature_version(environment.id, feature.id)
        if environment.use_v2_feature_versioning
        else None
    )
    highest_priority: int | None = FeatureSegment.objects.filter(
        environment=environment,
        feature=feature,
        environment_feature_version=version,
    ).aggregate(highest_priority=Max("priority"))["highest_priority"]
    return 0 if highest_priority is None else highest_priority + 1


def writes_live_segment_override(feature_state_data: LegacyFeatureStateData) -> bool:
    """Whether feature state data, validated by a legacy API, is for a live override.

    TODO: Remove after https://github.com/Flagsmith/flagsmith/issues/7641
    """
    live_from = feature_state_data.get("live_from")
    return (
        feature_state_data.get("identity") is None
        and feature_state_data.get("environment_feature_version") is None
        and feature_state_data.get("change_request") is None
        and (live_from is None or live_from <= timezone.now())
    )


def write_segment_override(
    *,
    environment: Environment,
    feature: Feature,
    segment_id: int,
    feature_state_data: LegacyFeatureStateData,
    author: AuthorData,
    priority: int | None = None,
) -> FeatureState:
    """Write a live override through the flag API, from data validated by a
    legacy API, notifying VCS integrations.

    TODO: Remove after https://github.com/Flagsmith/flagsmith/issues/7641
    """
    with transaction.atomic():
        update_flag(
            environment=environment,
            feature=feature,
            changes={
                "segment_overrides": [
                    map_feature_state_data_to_segment_override(
                        feature, segment_id, feature_state_data, priority=priority
                    )
                ]
            },
            replace=False,
            author=author,
            overwrite_system_segment_overrides=False,
        )
        feature_state = get_segment_override(
            environment=environment, feature=feature, segment_id=segment_id
        )
        assert feature_state is not None
        feature_state_value = feature_state.feature_state_value
        if clears_legacy_flag_value(feature_state_data) and (
            map_flag_value(feature_state_value) is not None
        ):
            # Legacy APIs write overrides directly only without v2 feature
            # versioning, so clearing values in place doesn't bypass it.
            feature_state_value.string_value = None
            feature_state_value.integer_value = None
            feature_state_value.boolean_value = None
            feature_state_value.save()
    dispatch_vcs_on_feature_state_changed(feature_state)
    return feature_state


def is_segment_override_unchanged(
    feature_segment: FeatureSegment,
    feature_state: FeatureState,
    feature_state_data: LegacyFeatureStateData,
) -> bool:
    """Whether writing data, validated by a legacy API, leaves an override as it is.

    TODO: Remove after https://github.com/Flagsmith/flagsmith/issues/7641
    """
    changes = map_feature_state_data_to_segment_override(
        feature_segment.feature, feature_segment.segment_id, feature_state_data
    )
    value = map_flag_value(feature_state.feature_state_value)
    weights = {
        multivariate_value.multivariate_feature_option_id: (
            multivariate_value.percentage_allocation
        )
        for multivariate_value in feature_state.multivariate_feature_state_values.all()
    }
    new_value = (
        None
        if clears_legacy_flag_value(feature_state_data)
        else changes.get("value", value)
    )
    return (
        changes.get("enabled", feature_state.enabled) == feature_state.enabled
        and new_value == value
        and all(
            weights.get(variant["id"], 0) == variant["weight"]
            for variant in changes.get("variants", [])
        )
    )
