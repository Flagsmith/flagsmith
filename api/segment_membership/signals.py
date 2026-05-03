"""Signal handlers maintaining the segment membership index.

Handlers stay strictly synchronous on the request path: they only enqueue
async tasks via `flagsmith-task-processor`. The actual bitmap work happens in
`segment_membership.tasks`. This keeps the user-facing write path clear of
ordinal allocation, atom evaluation, and bitmap I/O.

Tasks are idempotent (each reads current state and recomputes bits), so
out-of-order delivery and at-least-once retries converge correctly.
"""

from typing import Any

import structlog
from django.conf import settings
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from environments.identities.models import Identity
from environments.identities.signals import traits_changed
from environments.identities.traits.models import Trait
from segment_membership import tasks
from segments.models import Segment

logger = structlog.get_logger("segment_membership")


def _enabled() -> bool:
    return getattr(settings, "SEGMENT_MEMBERSHIP_ENABLED", False)


@receiver(post_save, sender=Identity)
def _identity_post_save(
    sender: type[Identity],
    instance: Identity,
    created: bool,
    **kwargs: Any,
) -> None:
    if not _enabled() or not created:
        return
    tasks.process_identity_created.delay(kwargs={"identity_id": instance.id})


@receiver(post_delete, sender=Identity)
def _identity_post_delete(
    sender: type[Identity],
    instance: Identity,
    **kwargs: Any,
) -> None:
    if not _enabled():
        return
    tasks.process_identity_deleted.delay(
        kwargs={
            "identity_id": instance.id,
            "environment_id": instance.environment_id,
        }
    )


@receiver(post_save, sender=Trait)
def _trait_post_save(
    sender: type[Trait],
    instance: Trait,
    created: bool,
    **kwargs: Any,
) -> None:
    if not _enabled():
        return
    tasks.process_traits_changed.delay(
        kwargs={
            "identity_id": instance.identity_id,
            "changed_keys": [instance.trait_key],
        }
    )


@receiver(post_delete, sender=Trait)
def _trait_post_delete(
    sender: type[Trait],
    instance: Trait,
    **kwargs: Any,
) -> None:
    if not _enabled():
        return
    tasks.process_traits_changed.delay(
        kwargs={
            "identity_id": instance.identity_id,
            "changed_keys": [instance.trait_key],
        }
    )


@receiver(traits_changed)
def _traits_changed(
    sender: type[Identity],
    instance: Identity,
    changed_keys: set[str],
    **kwargs: Any,
) -> None:
    """Bulk write paths in `Identity.update_traits` and
    `Identity.generate_traits(persist=True)` bypass `post_save`. This handler
    enqueues the maintenance task for the union of keys those paths report."""
    if not _enabled():
        return
    if not changed_keys:
        return
    tasks.process_traits_changed.delay(
        kwargs={
            "identity_id": instance.id,
            "changed_keys": list(changed_keys),
        }
    )


@receiver(post_save, sender=Segment)
def _segment_post_save(
    sender: type[Segment],
    instance: Segment,
    created: bool,
    **kwargs: Any,
) -> None:
    """A canonical segment was created or edited. Edits go through
    `serializer.update()` which mutates the canonical row in place after
    snapshotting a non-canonical revision; we filter to canonical rows by
    `version_of_id == id`, so the snapshot saves don't trigger backfill."""
    if not _enabled():
        return
    if instance.version_of_id != instance.id:
        return
    tasks.process_segment_canonical_changed.delay(
        kwargs={"segment_id": instance.id},
    )
