from datetime import datetime

from django.db import models
from softdelete.models import SoftDeleteObject  # type: ignore[import-untyped]

from api_keys.models import MasterAPIKey
from organisations.models import Organisation
from trust_relationships.types import ClaimRule
from users.models import FFAdminUser


class TrustRelationship(SoftDeleteObject):  # type: ignore[misc]
    organisation: models.ForeignKey[Organisation, Organisation] = models.ForeignKey(
        Organisation,
        on_delete=models.CASCADE,
        related_name="trust_relationships",
    )
    name: models.CharField[str, str] = models.CharField(
        max_length=100,
        help_text="Display name for this trust relationship.",
    )
    issuer: models.URLField[str, str] = models.URLField(
        max_length=500,
        help_text="OIDC issuer URL expected in exchanged tokens' `iss` claim.",
    )
    audience: models.CharField[str, str] = models.CharField(
        max_length=500,
        help_text="Expected value of the `aud` claim in exchanged tokens.",
    )
    claim_rules: models.JSONField[list[ClaimRule], list[ClaimRule]] = models.JSONField(
        default=list,
        blank=True,
        help_text="Constraints an exchanged token's claims must satisfy.",
    )
    master_api_key: models.OneToOneField[MasterAPIKey, MasterAPIKey] = (
        models.OneToOneField(
            MasterAPIKey,
            on_delete=models.CASCADE,
            related_name="trust_relationship",
        )
    )
    created_by: models.ForeignKey[FFAdminUser | None, FFAdminUser | None] = (
        models.ForeignKey(FFAdminUser, on_delete=models.SET_NULL, null=True, blank=True)
    )
    created_at: models.DateTimeField[datetime, datetime] = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ("id",)
        constraints = [
            # Tokens are matched on (issuer, audience) at exchange time, so
            # a live pair must resolve to exactly one trust relationship.
            models.UniqueConstraint(
                fields=["issuer", "audience"],
                condition=models.Q(deleted_at__isnull=True),
                name="unique_live_issuer_audience",
            ),
        ]

    @property
    def is_admin(self) -> bool:
        return bool(self.master_api_key.is_admin)
