from django.db import models

from core.models import SoftDeleteExportableModel


class CohortSourceType(models.TextChoices):
    CSV = "csv", "CSV"


class Cohort(SoftDeleteExportableModel):
    environment = models.ForeignKey(
        "environments.Environment",
        on_delete=models.CASCADE,
        related_name="cohorts",
    )
    segment = models.ForeignKey(
        "segments.Segment",
        on_delete=models.CASCADE,
        related_name="cohorts",
    )
    source_type = models.CharField(
        max_length=50,
        choices=CohortSourceType.choices,
        default=CohortSourceType.CSV,
    )
    version = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)


class CohortMembershipState(models.TextChoices):
    PENDING_ADD = "pending_add", "Pending add"
    APPLIED = "applied", "Applied"
    PENDING_REMOVE = "pending_remove", "Pending remove"


class CohortMembership(models.Model):
    cohort = models.ForeignKey(
        Cohort,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    # Length mirrors Identity.identifier.
    identifier = models.CharField(max_length=2000)
    state = models.CharField(
        max_length=50,
        choices=CohortMembershipState.choices,
        default=CohortMembershipState.PENDING_ADD,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["cohort", "identifier"],
                name="unique_cohort_membership_identifier",
            ),
        ]
        indexes = [
            # Serves pending-state drains and per-identifier eval lookups.
            models.Index(fields=["cohort", "state"]),
        ]
