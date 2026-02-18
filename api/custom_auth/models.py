from django.db import models

from organisations.models import Organisation
from users.models import FFAdminUser


class UserPasswordResetRequest(models.Model):
    user = models.ForeignKey(
        FFAdminUser, related_name="password_reset_requests", on_delete=models.CASCADE
    )
    requested_at = models.DateTimeField(auto_now_add=True)


class OIDCConfiguration(models.Model):
    name = models.SlugField(unique=True, help_text="URL-friendly identifier for this OIDC configuration.")
    organisation = models.ForeignKey(
        Organisation, on_delete=models.CASCADE, related_name="oidc_configurations"
    )
    provider_url = models.URLField(
        help_text="The base URL of the OIDC provider (e.g., https://keycloak.example.com/realms/myrealm)."
    )
    client_id = models.CharField(max_length=200)
    client_secret = models.CharField(max_length=200)
    frontend_url = models.URLField(
        default="",
        blank=True,
        help_text="The base URL of the Flagsmith dashboard. Users will be redirected here after authentication.",
    )
    allow_idp_initiated = models.BooleanField(
        default=False,
        help_text="Allow logins initiated by the identity provider.",
    )

    def __str__(self) -> str:
        return self.name
