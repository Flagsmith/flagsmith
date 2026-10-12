from django.db.models import Max, Q

from environments.models import Environment
from features.models import Feature, FeatureSegment, FeatureState
from features.versioning.versioning_service import (
    get_current_live_environment_feature_version,
    get_environment_flags_list,
)


def get_segment_overrides(
    *, environment: Environment, feature: Feature
) -> dict[int, FeatureState]:
    """Get the flag's live overrides, by segment ID.

    TODO: Remove after https://github.com/Flagsmith/flagsmith/issues/7641
    """
    return {
        feature_state.feature_segment.segment_id: feature_state
        for feature_state in get_environment_flags_list(
            environment,
            additional_filters=Q(
                feature_id=feature.id,
                feature_segment__isnull=False,
                identity__isnull=True,
            ),
            additional_prefetch_related_args=["multivariate_feature_state_values"],
        )
        if feature_state.feature_segment
    }


def get_segment_override(
    *, environment: Environment, feature: Feature, segment_id: int
) -> FeatureState | None:
    """Get the flag's live override for a segment, if any.

    TODO: Remove after https://github.com/Flagsmith/flagsmith/issues/7641
    """
    return get_segment_overrides(environment=environment, feature=feature).get(
        segment_id
    )


def is_live_segment_override(feature_segment: FeatureSegment) -> bool:
    """Whether a feature segment is the one the flag serves its segment from.

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
    """Get the priority of an override added after the flag's other overrides."""
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
