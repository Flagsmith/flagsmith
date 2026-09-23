from django.db import models

from environments.models import Environment
from organisations.models import Organisation
from segments.models import Segment


class SegmentMembershipCount(models.Model):
    """Cached identity-match count for one (segment, environment) pair."""

    segment = models.ForeignKey(
        Segment,
        on_delete=models.CASCADE,
        related_name="membership_counts",
    )
    environment = models.ForeignKey(
        Environment,
        on_delete=models.CASCADE,
        related_name="+",
    )
    count = models.PositiveIntegerField()
    last_synced_at = models.DateTimeField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["segment", "environment"],
                name="segment_membership_count_unique_segment_environment",
            ),
        ]


class SegmentMembershipSeed(models.Model):
    """Tracks whether an organisation's existing identities have been mirrored
    into ClickHouse.

    `seeded_at` is null while a backfill is outstanding."""

    organisation = models.OneToOneField(
        Organisation,
        on_delete=models.CASCADE,
        related_name="+",
    )
    seeded_at = models.DateTimeField(null=True)
