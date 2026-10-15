from django.db import transaction
from django.db.models import F, Max, Q, QuerySet
from django.utils import timezone

from core.dataclasses import AuthorData
from environments.models import Environment
from features.feature_segments.mappers import (
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

    TODO: Remove after https://github.com/Flagsmith/flagsmith/issues/1667
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

    TODO: Remove after https://github.com/Flagsmith/flagsmith/issues/1667
    """
    override = get_segment_override(
        environment=feature_segment.environment,
        feature=feature_segment.feature,
        segment_id=feature_segment.segment_id,
    )
    return override is not None and override.feature_segment_id == feature_segment.id


def _get_feature_segments(
    environment: Environment, feature: Feature
) -> QuerySet[FeatureSegment]:
    version = (
        get_current_live_environment_feature_version(environment.id, feature.id)
        if environment.use_v2_feature_versioning
        else None
    )
    feature_segments: QuerySet[FeatureSegment] = FeatureSegment.objects.filter(
        environment=environment,
        feature=feature,
        environment_feature_version=version,
    )
    return feature_segments


def get_next_segment_override_priority(
    *, environment: Environment, feature: Feature
) -> int:
    highest_priority: int | None = _get_feature_segments(
        environment, feature
    ).aggregate(highest_priority=Max("priority"))["highest_priority"]
    return 0 if highest_priority is None else highest_priority + 1


def renumber_tied_segment_overrides(
    feature_segments: QuerySet[FeatureSegment],
) -> None:
    """Renumber overrides from 0, keeping their order, if any share a priority.

    Legacy APIs used to leave overrides sharing priorities, which the flag API
    refuses to write.

    TODO: Remove after https://github.com/Flagsmith/flagsmith/issues/1667
    """
    ordered = list(feature_segments.order_by("priority", "id"))
    if len({feature_segment.priority for feature_segment in ordered}) == len(ordered):
        return
    for priority, feature_segment in enumerate(ordered):
        feature_segment.priority = priority
    FeatureSegment.objects.bulk_update(ordered, ["priority"])


def _make_room_for_segment_override(
    *, feature_segments: QuerySet[FeatureSegment], segment_id: int, priority: int
) -> None:
    """Move the flag's other overrides from a priority on down, if it's taken.

    TODO: Remove after https://github.com/Flagsmith/flagsmith/issues/1667
    """
    others = feature_segments.exclude(segment_id=segment_id)
    if others.filter(priority=priority).exists():
        others.filter(priority__gte=priority).update(priority=F("priority") + 1)


def writes_live_segment_override(feature_state_data: LegacyFeatureStateData) -> bool:
    """Whether feature state data, validated by a legacy API, is for a live override.

    TODO: Remove after https://github.com/Flagsmith/flagsmith/issues/1667
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

    TODO: Remove after https://github.com/Flagsmith/flagsmith/issues/1667
    """
    with transaction.atomic():
        feature_segments = _get_feature_segments(environment, feature)
        renumber_tied_segment_overrides(feature_segments)
        if priority is not None:
            _make_room_for_segment_override(
                feature_segments=feature_segments,
                segment_id=segment_id,
                priority=priority,
            )
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
    dispatch_vcs_on_feature_state_changed(feature_state)
    return feature_state


def is_segment_override_unchanged(
    feature_segment: FeatureSegment,
    feature_state: FeatureState,
    feature_state_data: LegacyFeatureStateData,
) -> bool:
    """Whether writing data, validated by a legacy API, leaves an override as it is.

    TODO: Remove after https://github.com/Flagsmith/flagsmith/issues/1667
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
    return (
        changes.get("enabled", feature_state.enabled) == feature_state.enabled
        and changes.get("value", value) == value
        and all(
            weights.get(variant["id"], 0) == variant["weight"]
            for variant in changes.get("variants", [])
        )
    )
