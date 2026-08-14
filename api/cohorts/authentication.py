import typing
from contextlib import suppress

from rest_framework import authentication, exceptions
from rest_framework.request import Request

from cohorts.models import CohortSyncKey


class CohortSyncKeyUser:
    """Stand-in request user for machine calls authenticated by a
    CohortSyncKey; carries no permissions of its own."""

    # Named `sync_key`, not `key`: the audit signal that stamps history rows
    # duck-types master API keys via `request.user.key`.
    def __init__(self, sync_key: CohortSyncKey) -> None:
        self.sync_key = sync_key

    def __str__(self) -> str:
        return self.sync_key.name

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def pk(self) -> str:
        return self.sync_key.id

    @property
    def is_master_api_key_user(self) -> bool:
        # The discriminator history/audit code uses for machine callers:
        # without it, historical records try to store this object as the
        # acting FFAdminUser and fail.
        return True


class CohortSyncKeyAuthentication(authentication.BaseAuthentication):
    def authenticate(
        self, request: Request
    ) -> tuple[CohortSyncKeyUser, CohortSyncKey] | None:
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return None

        with suppress(CohortSyncKey.DoesNotExist):
            key = typing.cast(
                CohortSyncKey,
                CohortSyncKey.objects.get_from_key(header.removeprefix("Bearer ")),
            )
            if not key.has_expired:
                return CohortSyncKeyUser(key), key

        raise exceptions.AuthenticationFailed("Valid cohort sync key not found.")

    def authenticate_header(self, request: Request) -> str:
        # Makes missing credentials a 401 rather than DRF's default 403.
        return "Bearer"
