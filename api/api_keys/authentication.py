from rest_framework import authentication, exceptions
from rest_framework_api_key.permissions import KeyParser

from api_keys.models import MasterAPIKey
from api_keys.user import APIKeyUser

key_parser = KeyParser()


class MasterAPIKeyAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        key = key_parser.get(request)
        try:
            key = MasterAPIKey.objects.get_from_key(key)
        except MasterAPIKey.DoesNotExist:
            raise exceptions.AuthenticationFailed("Valid Master API Key not found.")

        user = APIKeyUser(key)
        return (user, None)
