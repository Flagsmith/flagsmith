from django.db import models
from rest_framework_api_key.models import AbstractAPIKey, APIKeyManager

from cohorts.constants import COHORT_SYSTEM_TRAIT_KEY_PREFIX
from core.models import SoftDeleteExportableModel


class CohortSourceType(models.TextChoices):
    CSV = "csv", "CSV"
    AMPLITUDE = "amplitude", "Amplitude"


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
    # Deletion drains memberships from the identity store first; the cohort is
    # only soft-deleted once drained. This marks it as awaiting that final step.
    deletion_requested_at = models.DateTimeField(null=True, blank=True)

    @property
    def system_trait_key(self) -> str:
        return f"{COHORT_SYSTEM_TRAIT_KEY_PREFIX}{self.uuid}"

    class Meta:
        constraints = [
            # Exactly one active cohort feeds a segment: two cohorts on one
            # segment would race each other's membership sync.
            models.UniqueConstraint(
                fields=["segment"],
                condition=models.Q(deleted_at__isnull=True),
                name="unique_active_cohort_per_segment",
            ),
        ]


class CohortSyncKeyManager(APIKeyManager):
    pass


class CohortSyncKey(AbstractAPIKey):
    """Bearer credential an external cohort source uses to call the
    cohort-sync endpoints; scopes every call to one environment."""

    environment = models.ForeignKey(
        "environments.Environment",
        on_delete=models.CASCADE,
        related_name="cohort_sync_keys",
    )
    created_by = models.ForeignKey(
        "users.FFAdminUser", on_delete=models.SET_NULL, null=True, blank=True
    )

    objects = CohortSyncKeyManager()  # type: ignore[misc]


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
