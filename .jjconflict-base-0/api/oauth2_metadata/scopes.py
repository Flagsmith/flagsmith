from typing import Any

from oauth2_provider.models import Application
from oauth2_provider.scopes import SettingsScopes

from oauth2_metadata.constants import (
    FIRST_PARTY_CLIENT_IDS,
    FIRST_PARTY_SCOPES,
    THIRD_PARTY_SCOPES,
)


class FlagsmithScopes(SettingsScopes):  # type: ignore[misc]
    """Per-client scope issuance policy."""

    def get_allowed_scopes(
        self,
        application: Application | None = None,
    ) -> frozenset[str]:
        if application is not None:
            if application.client_id in FIRST_PARTY_CLIENT_IDS:
                return FIRST_PARTY_SCOPES
        return THIRD_PARTY_SCOPES

    def get_available_scopes(
        self,
        application: Application | None = None,
        request: Any = None,
        *args: Any,
        **kwargs: Any,
    ) -> list[str]:
        """What may a client request."""
        allowed_scopes = self.get_allowed_scopes(application)
        scopes: list[str] = super().get_available_scopes(
            application, request, *args, **kwargs
        )
        return [scope for scope in scopes if scope in allowed_scopes]

    def get_default_scopes(
        self,
        application: Application | None = None,
        request: Any = None,
        *args: Any,
        **kwargs: Any,
    ) -> list[str]:
        """What does a client get when it doesn't request for any particular scopes."""
        allowed_scopes = self.get_allowed_scopes(application)
        scopes: list[str] = super().get_default_scopes(
            application, request, *args, **kwargs
        )
        return [scope for scope in scopes if scope in allowed_scopes]
