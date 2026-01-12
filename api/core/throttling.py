from typing import TYPE_CHECKING

from django.conf import settings
from django.core.cache import caches
from rest_framework import throttling
from rest_framework.request import Request

from api_keys.user import APIKeyUser

if TYPE_CHECKING:
    from rest_framework.views import APIView


class UserRateThrottle(throttling.UserRateThrottle):
    cache = caches[settings.USER_THROTTLE_CACHE_NAME]


class MasterAPIKeyUserRateThrottle(throttling.UserRateThrottle):
    cache = caches[settings.USER_THROTTLE_CACHE_NAME]

    def get_cache_key(self, request: Request, view: "APIView") -> str | None:
        if getattr(request.user, "is_master_api_key_user", False):
            assert isinstance(request.user, APIKeyUser)
            return self.cache_format % {
                "scope": self.scope,
                "ident": str(request.user.key.id),
            }
        return None
