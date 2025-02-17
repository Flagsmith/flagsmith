from core.request_origin import RequestOrigin
from django.conf import settings
from django.core.cache import caches
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from environments.api_keys import SERVER_API_KEY_PREFIX
from environments.models import Environment

environment_cache = caches[settings.ENVIRONMENT_CACHE_NAME]


class EnvironmentKeyAuthentication(BaseAuthentication):
    """
    Custom authentication class to add the environment to the request for
    endpoints used by the clients.
    """

    def __init__(self, *args, required_key_prefix: str = "", **kwargs):  # type: ignore[no-untyped-def]
        super(EnvironmentKeyAuthentication, self).__init__(*args, **kwargs)
        self.required_key_prefix = required_key_prefix

    def authenticate(self, request):  # type: ignore[no-untyped-def]
        api_key = request.META.get("HTTP_X_ENVIRONMENT_KEY")
        if not (api_key and api_key.startswith(self.required_key_prefix)):
            raise AuthenticationFailed("Invalid or missing Environment key")

        environment = Environment.get_from_cache(api_key)  # type: ignore[no-untyped-call]
        if not environment:
            raise AuthenticationFailed("Invalid or missing Environment Key")

        if environment.project.organisation.stop_serving_flags:
            raise AuthenticationFailed("Organisation is disabled from serving flags.")

        request.environment = environment
        request.originated_from = (
            RequestOrigin.SERVER
            if api_key.startswith(SERVER_API_KEY_PREFIX)
            else RequestOrigin.CLIENT
        )

        # DRF authentication expects a two tuple to be returned containing User, auth
        return None, None
