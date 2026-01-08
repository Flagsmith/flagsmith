import typing

from django.conf import settings
from django.core.cache import caches
from redis.exceptions import RedisClusterException
from rest_framework import throttling

if typing.TYPE_CHECKING:
    from rest_framework.request import Request
    from rest_framework.views import APIView


class UserRateThrottle(throttling.UserRateThrottle):
    cache = caches[settings.USER_THROTTLE_CACHE_NAME]

    def allow_request(
        self, request: "Request", view: "APIView"
    ) -> bool:  # pragma: no cover
        try:
            return super(UserRateThrottle, self).allow_request(request, view)
        except RedisClusterException:
            # Handle intermittent redis connection failures.
            # Allow the request without calling throttle_success which
            # would also try to establish a connection to Redis.
            return True
