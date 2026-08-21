from django.db import models
from rest_framework_api_key.models import AbstractAPIKey

from cohorts.constants import COHORT_SYSTEM_TRAIT_KEY_PREFIX
from core.models import SoftDeleteExportableModel


class CohortSourceType(models.TextChoices):
    CSV = "csv", "CSV"
    AMPLITUDE = "amplitude", "Amplitude"
    MIXPANEL = "mixpanel", "Mixpanel"


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
    # The cohort's identifier in the external source (e.g. Mixpanel's cohort
    # ID). Set for sources that push to us under their own identifier; null
    # for sources that adopt ours (Amplitude) and for CSV cohorts.
    external_id = models.CharField(max_length=255, null=True, blank=True)
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
            # One Mixpanel cohort must map to one active cohort per
            # environment: without this, two simultaneous first-sync requests
            # would each create their own cohort and split the members
            # between them.
            models.UniqueConstraint(
                fields=["environment", "source_type", "external_id"],
                condition=models.Q(deleted_at__isnull=True, external_id__isnull=False),
                name="unique_active_cohort_per_source_external_id",
            ),
        ]


class CohortSyncKey(AbstractAPIKey):
    environment = models.ForeignKey(
        "environments.Environment",
        on_delete=models.CASCADE,
        related_name="cohort_sync_keys",
    )
    created_by = models.ForeignKey(
        "users.FFAdminUser", on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta(AbstractAPIKey.Meta):
        verbose_name = "cohort sync key"
        verbose_name_plural = "cohort sync keys"


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
