from django.db import models

from environments.models import Environment
from segments.models import Segment


class SegmentMembership(models.Model):
    """
    Cached count of identities matching a canonical segment within a
    single environment. One row per (segment, environment) pair.
    """

    segment = models.ForeignKey(
        Segment,
        on_delete=models.CASCADE,
        related_name="memberships",
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
                name="segment_membership_unique_segment_environment",
            ),
        ]
