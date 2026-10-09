from django.db.models import Max, Q
from django.utils import timezone
from rest_framework.request import Request

from audit.tasks import create_segment_priorities_changed_audit_log
from environments.models import Environment
from features.models import Feature, FeatureSegment, FeatureState
from features.versioning.versioning_service import (
    get_current_live_environment_feature_version,
    get_environment_flags_list,
)


def get_reordered_priorities(
    feature_segments: list[FeatureSegment],
    new_priorities: dict[int, int],
) -> dict[int, int]:
    """Get the priorities `FeatureSegment.update_priorities` would leave the
    feature segments with, by feature segment ID.

    Moving a feature segment to a priority moves the ones in between out of
    its way, as the requested moves are made in the order of their priorities.

    TODO: Remove after https://github.com/Flagsmith/flagsmith/issues/7641
    """
    priorities = {
        feature_segment.id: feature_segment.priority
        for feature_segment in feature_segments
    }
    # Each move reads its feature segment's priority as it was at first.
    initial_priorities = priorities.copy()
    for feature_segment_id in sorted(
        new_priorities, key=lambda id_: (initial_priorities[id_], id_)
    ):
        old_priority = initial_priorities[feature_segment_id]
        new_priority = new_priorities[feature_segment_id]
        if old_priority == new_priority:
            continue
        for other_id, priority in priorities.items():
            if new_priority <= priority < old_priority:
                priorities[other_id] = priority + 1
            elif old_priority < priority <= new_priority:
                priorities[other_id] = priority - 1
        priorities[feature_segment_id] = new_priority
    return priorities


def create_priorities_changed_audit_log(
    request: Request,
    previous_priorities: list[tuple[int, int]],
    feature_segment_ids: list[int],
) -> None:
    """Audit a reordering of segment overrides, as `update_priorities` does.

    TODO: Remove after https://github.com/Flagsmith/flagsmith/issues/7641
    """
    create_segment_priorities_changed_audit_log.delay(
        kwargs={
            "previous_id_priority_pairs": previous_priorities,
            "feature_segment_ids": feature_segment_ids,
            "user_id": getattr(request.user, "id", None),
            "master_api_key_id": (
                request.master_api_key.id
                if hasattr(request, "master_api_key")
                else None
            ),
            "changed_at": timezone.now().isoformat(),
        }
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
    """Get the priority of an override added after the flag's other overrides.

    TODO: Remove after https://github.com/Flagsmith/flagsmith/issues/7641
    """
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
