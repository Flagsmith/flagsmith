from django.conf import settings
from django.core.cache import caches
from rest_framework import throttling


class UserRateThrottle(throttling.UserRateThrottle):
    cache = caches[settings.USER_THROTTLE_CACHE_NAME]
