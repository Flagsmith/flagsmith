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

import json
import os
import typing

from django.conf import settings
from flagsmith import Flagsmith
from flagsmith.models import DefaultFlag, Flags

_flagsmith_client: typing.Optional["_WrappedFlagsmith"] = None
_defaults: typing.Dict[str, DefaultFlag] = {}
_FLAGSMITH_ENABLED: bool = settings.FLAGSMITH_SERVER_KEY is not None


def get_client() -> Flagsmith:
    global _flagsmith_client, _defaults

    if not _flagsmith_client:
        _defaults = _build_defaults()
        _flagsmith_client = _WrappedFlagsmith(
            environment_key=settings.FLAGSMITH_SERVER_KEY,
            api_url=settings.FLAGSMITH_API_URL,
            default_flag_handler=_default_handler,
        )

    return _flagsmith_client


class _WrappedFlagsmith(Flagsmith):
    """
    Wrap the flagsmith class so that we can immediately return an empty set of flags
    (with the default handler) when flagsmith is not enabled. This prevents the client
    from trying to make a network request and failing. Since we don't want people to
    have to use Flagsmith on Flagsmith in the API, we need this extra logic.
    """

    def __init__(self, *args, **kwargs):
        if not _FLAGSMITH_ENABLED:
            return

        super().__init__(*args, **kwargs)

    def get_environment_flags(self) -> Flags:
        if not _FLAGSMITH_ENABLED:
            return Flags(flags={}, default_flag_handler=_default_handler)

        return super().get_environment_flags()

    def get_identity_flags(
        self, identifier: str, traits: typing.Dict[str, typing.Any] = None
    ) -> Flags:
        if not _FLAGSMITH_ENABLED:
            return Flags(flags={}, default_flag_handler=_default_handler)

        return super().get_identity_flags(identifier, traits)


def _default_handler(feature_name: str) -> DefaultFlag:
    return _defaults.get(feature_name)


def _build_defaults() -> typing.Dict[str, DefaultFlag]:
    with open(
        os.path.join(settings.BASE_DIR, "integrations/flagsmith/defaults.json")
    ) as defaults:
        return {
            flag["feature"]["name"]: DefaultFlag(
                enabled=flag["enabled"], value=flag["feature_state_value"]
            )
            for flag in json.loads(defaults.read())
        }
