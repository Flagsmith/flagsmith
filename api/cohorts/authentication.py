import base64
from contextlib import suppress

from django.contrib.auth.models import AnonymousUser
from rest_framework import authentication, exceptions
from rest_framework.request import Request

from cohorts.models import CohortSyncKey


class CohortSyncKeyAuthentication(authentication.BaseAuthentication):
    """
    Accepts a cohort sync key sent either as a Bearer token or as the
    password of Basic credentials. Amplitude sends Bearer; Mixpanel's
    webhook setup only offers a username/password form, so its customers
    enter any username and the key as the password. The username is
    ignored.
    """

    def authenticate(
        self, request: Request
    ) -> tuple[AnonymousUser, CohortSyncKey] | None:
        header = request.headers.get("Authorization", "")
        if header.startswith("Bearer "):
            raw_key = header.removeprefix("Bearer ")
        elif header.startswith("Basic "):
            try:
                decoded = base64.b64decode(
                    header.removeprefix("Basic "), validate=True
                ).decode()
            except ValueError:
                # Covers malformed base64, header bytes outside ASCII, and
                # decoded credentials that are not valid UTF-8.
                raise exceptions.AuthenticationFailed("Invalid Basic credentials.")
            # Split at the first colon, so a key containing colons survives.
            _, _, raw_key = decoded.partition(":")
        else:
            return None

        with suppress(CohortSyncKey.DoesNotExist):
            key = CohortSyncKey.objects.get_from_key(raw_key)
            if not key.has_expired:
                # No person is acting here, so no user is returned: the key
                # alone carries authority, and audit trails record the source
                # rather than a user.
                return AnonymousUser(), key

        raise exceptions.AuthenticationFailed("Valid cohort sync key not found.")

    def authenticate_header(self, request: Request) -> str:
        # Makes missing or invalid credentials a 401 rather than DRF's default 403.
        return "Bearer"
