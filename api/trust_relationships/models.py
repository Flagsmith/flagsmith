from django.db import models
from softdelete.models import SoftDeleteObject  # type: ignore[import-untyped]

from api_keys.models import MasterAPIKey
from organisations.models import Organisation


class TrustRelationship(SoftDeleteObject):  # type: ignore[misc]
    organisation = models.ForeignKey(  # type: ignore[var-annotated]
        Organisation,
        on_delete=models.CASCADE,
        related_name="trust_relationships",
    )
    name = models.CharField(  # type: ignore[var-annotated]
        max_length=100,
        help_text="Display name for this trust relationship.",
    )
    issuer = models.URLField(  # type: ignore[var-annotated]
        max_length=500,
        help_text="OIDC issuer URL expected in exchanged tokens' `iss` claim.",
    )
    audience = models.CharField(  # type: ignore[var-annotated]
        max_length=500,
        help_text="Expected value of the `aud` claim in exchanged tokens.",
    )
    claim_rules = models.JSONField(default=list, blank=True)
    master_api_key = models.OneToOneField(  # type: ignore[var-annotated]
        MasterAPIKey,
        on_delete=models.CASCADE,
        related_name="trust_relationship",
    )
    created_by = models.ForeignKey(  # type: ignore[var-annotated]
        "users.FFAdminUser", on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)  # type: ignore[var-annotated]

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
