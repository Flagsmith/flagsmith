from typing import TYPE_CHECKING

from django.conf import settings
from django.core.cache import caches
from rest_framework import throttling
from rest_framework.request import Request

if TYPE_CHECKING:
    from rest_framework.views import APIView


class MasterAPIKeyUserRateThrottle(throttling.UserRateThrottle):
    cache = caches[settings.USER_THROTTLE_CACHE_NAME]

    def allow_request(self, request: Request, view: "APIView") -> bool:
        if not getattr(request.user, "is_master_api_key_user", False):
            return True
        return super().allow_request(request, view)
