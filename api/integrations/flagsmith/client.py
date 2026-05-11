"""
OpenFeature client wrapper for Flagsmith on Flagsmith feature evaluation.

Usage:

```
from integrations.flagsmith.client import get_openfeature_client

client = get_openfeature_client()
enabled = client.get_boolean_value(
    "flag_name", default_value=False, evaluation_context=ctx
)
```
"""

import typing

import openfeature.api as openfeature_api
from django.conf import settings
from flagsmith import Flagsmith
from flagsmith.offline_handlers import LocalFileHandler
from openfeature.client import OpenFeatureClient
from openfeature_flagsmith.provider import FlagsmithProvider

from integrations.flagsmith.exceptions import FlagsmithIntegrationError
from integrations.flagsmith.flagsmith_service import ENVIRONMENT_JSON_PATH

DEFAULT_OPENFEATURE_DOMAIN = "flagsmith-api"


def get_openfeature_client(
    domain: str = DEFAULT_OPENFEATURE_DOMAIN,
) -> OpenFeatureClient:
    openfeature_client = openfeature_api.get_client(domain=domain)
    # An unbound domain falls back to a ready `NoOpProvider`, so we can't rely
    # on provider status here — check whether we're still on the default.
    metadata = openfeature_api.get_provider_metadata(domain)
    if getattr(metadata, "is_default_provider", False):
        initialise_provider(domain, **get_provider_kwargs())
    return openfeature_client


def initialise_provider(
    domain: str = DEFAULT_OPENFEATURE_DOMAIN,
    **kwargs: typing.Any,
) -> None:
    flagsmith_client = Flagsmith(**kwargs)
    provider = FlagsmithProvider(client=flagsmith_client)
    openfeature_api.set_provider(provider, domain=domain)


def get_provider_kwargs() -> dict[str, typing.Any]:
    common_kwargs: dict[str, typing.Any] = {
        "offline_handler": LocalFileHandler(ENVIRONMENT_JSON_PATH),
        "enable_local_evaluation": True,
    }

    if settings.FLAGSMITH_ON_FLAGSMITH_SERVER_OFFLINE_MODE:
        return {"offline_mode": True, **common_kwargs}
    elif (
        settings.FLAGSMITH_ON_FLAGSMITH_SERVER_KEY
        and settings.FLAGSMITH_ON_FLAGSMITH_SERVER_API_URL
    ):
        return {
            "environment_key": settings.FLAGSMITH_ON_FLAGSMITH_SERVER_KEY,
            "api_url": settings.FLAGSMITH_ON_FLAGSMITH_SERVER_API_URL,
            **common_kwargs,
        }

    raise FlagsmithIntegrationError(
        "Must either use offline mode, or provide "
        "FLAGSMITH_ON_FLAGSMITH_SERVER_KEY and FLAGSMITH_ON_FLAGSMITH_SERVER_API_URL."
    )
