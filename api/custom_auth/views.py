from djoser.views import UserViewSet
from rest_framework.throttling import ScopedRateThrottle
from trench.views.authtoken import (
    AuthTokenLoginOrRequestMFACode,
    AuthTokenLoginWithMFACode,
)


class CustomAuthTokenLoginOrRequestMFACode(AuthTokenLoginOrRequestMFACode):
    """
    Class to handle throttling for login requests
    """

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"


class CustomAuthTokenLoginWithMFACode(AuthTokenLoginWithMFACode):
    """
    Override class to add throttling
    """

    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "mfa_code"


class ThrottledUserViewSet(UserViewSet):
    throttle_scope = "signup"

    def get_throttles(self):
        """
        Used for throttling create(signup) action
        """
        throttles = []
        if self.action == "create":
            throttles = [ScopedRateThrottle()]
        return throttles
