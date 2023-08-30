from django.core.cache import caches
from rest_framework.throttling import UserRateThrottle


class DBBackedUserRateThrottle(UserRateThrottle):
    cache = caches["throttle-cache"]
    scope = "user"
