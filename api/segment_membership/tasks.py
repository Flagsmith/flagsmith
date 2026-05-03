"""Async maintenance tasks for the segment membership index.

Signal handlers in `signals.py` enqueue these tasks. The actual bitmap work
(ordinal allocation, atom evaluation, bitmap rewrites) runs in the task
processor — off the user-facing write path. Transactional correctness inside
the tasks is fine because the tasks are not on a hot path.

Tasks are idempotent by construction: each handler reads current state and
recomputes the bit value, so re-runs and out-of-order delivery converge to
the correct answer.
"""

from typing import Iterable

import structlog
from task_processor.decorators import register_task_handler

from environments.identities.models import Identity
from environments.models import Environment
from segment_membership import services
from segments.models import Segment

logger = structlog.get_logger("segment_membership")


@register_task_handler()
def process_identity_created(*, identity_id: int) -> None:
    """Allocate an ordinal and evaluate identifier/identity-key atoms for a
    newly-created identity."""
    try:
        identity = Identity.objects.select_related("environment").get(id=identity_id)
    except Identity.DoesNotExist:
        # Identity was deleted between enqueue and execute. Nothing to do.
        return
    services.on_identity_created(identity)


@register_task_handler()
def process_traits_changed(
    *,
    identity_id: int,
    changed_keys: Iterable[str],
) -> None:
    """Re-evaluate every atom whose property is among `changed_keys` against
    the identity's current trait state."""
    try:
        identity = Identity.objects.select_related("environment").get(id=identity_id)
    except Identity.DoesNotExist:
        return
    services.on_traits_changed(identity, list(changed_keys))


@register_task_handler()
def process_identity_deleted(*, identity_id: int, environment_id: int) -> None:
    """Clear the deleted identity's bit from every atom in its environment."""
    services.on_identity_deleted(identity_id, environment_id)


@register_task_handler()
def process_segment_canonical_changed(*, segment_id: int) -> None:
    """A canonical Segment row was created or its rules edited. Ensure the
    segment's atoms exist and backfill any new bitmaps in every env in the
    project. Atoms that drop out of the segment as a result of an edit are
    left in place (orphans); see the RFC's catalogue-maintenance section."""
    try:
        segment = Segment.live_objects.select_related("project").get(id=segment_id)
    except Segment.DoesNotExist:
        # Either deleted before the task ran, or the row is no longer canonical.
        return
    for environment in Environment.objects.filter(project=segment.project):
        services.backfill_segment(environment, segment)
