from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.conf import settings


@dataclass(frozen=True)
class OAuthConfig:
    """Base OAuth configuration derived from Django settings."""

    api_url: str
    frontend_url: str
    scopes: dict[str, str]

    @classmethod
    def from_settings(cls) -> OAuthConfig:
        oauth2_provider: dict[str, Any] = settings.OAUTH2_PROVIDER
        return cls(
            api_url=settings.FLAGSMITH_API_URL.rstrip("/"),
            frontend_url=settings.FLAGSMITH_FRONTEND_URL.rstrip("/"),
            scopes=oauth2_provider.get("SCOPES", {}),
        )
