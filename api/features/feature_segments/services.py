from django.utils import timezone
from rest_framework.request import Request

from audit.tasks import create_segment_priorities_changed_audit_log
from features.models import FeatureSegment


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
