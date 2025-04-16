import hashlib

from django.conf import settings
from django.core.cache import caches
from django.views import View
from rest_framework.request import Request
from rest_framework.throttling import BaseThrottle

from core.helpers import get_ip_address_from_request


class OnboardingRequestThrottle(BaseThrottle):
    cache = caches[settings.ONBOARDING_REQUEST_THROTTLE_CACHE_NAME]

    def get_cache_key(self, request: Request) -> str:
        return self.get_ip_hash(request)

    def get_ip_hash(self, request: Request) -> str:
        ip = get_ip_address_from_request(request)
        return hashlib.sha256(ip.encode()).hexdigest()  # type: ignore[union-attr]

    def allow_request(self, request: Request, view: View) -> bool:
        cache_key = self.get_cache_key(request)
        if self.cache.get(cache_key):
            return False

        self.cache.set(cache_key, 1)

        return True
