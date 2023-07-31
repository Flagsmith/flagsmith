"""
Wrapper module for the flagsmith client to implement singleton behaviour and provide some
additional logic by wrapping the client.

Usage:

```
environment_flags = get_client().get_environment_flags()
identity_flags = get_client().get_identity_flags()
```

Possible extensions:
 - Allow for multiple clients?
"""
import typing

from django.conf import settings
from flagsmith import Flagsmith
from flagsmith.offline_handlers import LocalFileHandler

from integrations.flagsmith.flagsmith_service import ENVIRONMENT_JSON_PATH

_flagsmith_client: typing.Optional["Flagsmith"] = None


def get_client() -> Flagsmith:
    global _flagsmith_client

    if not _flagsmith_client:
        _flagsmith_client = Flagsmith(**_get_client_kwargs())

    return _flagsmith_client


def _get_client_kwargs() -> dict[str, typing.Any]:
    _default_kwargs = {"offline_handler": LocalFileHandler(ENVIRONMENT_JSON_PATH)}

    if settings.FLAGSMITH_OFFLINE_MODE:
        return {"offline_mode": True, **_default_kwargs}
    elif (
        settings.FLAGSMITH_ON_FLAGSMITH_SERVER_KEY
        and settings.FLAGSMITH_ON_FLAGSMITH_SERVER_API_URL
    ):
        return {
            "environment_key": settings.FLAGSMITH_ON_FLAGSMITH_SERVER_KEY,
            "api_url": settings.FLAGSMITH_ON_FLAGSMITH_SERVER_API_URL,
            **_default_kwargs,
        }

    raise ValueError(
        "Must either use offline mode, or provide "
        "FLAGSMITH_ON_FLAGSMITH_SERVER_KEY and FLAGSMITH_ON_FLAGSMITH_SERVER_API_URL."
    )
