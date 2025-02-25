from contextlib import suppress

from rest_framework import authentication, exceptions
from rest_framework_api_key.permissions import KeyParser

from api_keys.models import MasterAPIKey
from api_keys.user import APIKeyUser

key_parser = KeyParser()


class MasterAPIKeyAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):  # type: ignore[no-untyped-def]
        key = key_parser.get(request)
        if not key:
            return None

        with suppress(MasterAPIKey.DoesNotExist):
            key = MasterAPIKey.objects.get_from_key(key)  # type: ignore[assignment]
            if not key.has_expired:  # type: ignore[attr-defined]
                return APIKeyUser(key), None  # type: ignore[arg-type]

        raise exceptions.AuthenticationFailed("Valid Master API Key not found.")
