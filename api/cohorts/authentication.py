import typing
from contextlib import suppress

from django.contrib.auth.models import AnonymousUser
from rest_framework import authentication, exceptions
from rest_framework.request import Request

from cohorts.models import CohortSyncKey


class CohortSyncKeyAuthentication(authentication.BaseAuthentication):
    def authenticate(
        self, request: Request
    ) -> tuple[AnonymousUser, CohortSyncKey] | None:
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return None

        with suppress(CohortSyncKey.DoesNotExist):
            key = typing.cast(
                CohortSyncKey,
                CohortSyncKey.objects.get_from_key(header.removeprefix("Bearer ")),
            )
            if not key.has_expired:
                # No person is acting here, so no user is returned: the key
                # alone carries authority, and audit trails record the source
                # rather than a user.
                return AnonymousUser(), key

        raise exceptions.AuthenticationFailed("Valid cohort sync key not found.")

    def authenticate_header(self, request: Request) -> str:
        # Makes missing or invalid credentials a 401 rather than DRF's default 403.
        return "Bearer"
