from rest_framework.throttling import ScopedRateThrottle
from trench.views.authtoken import AuthTokenLoginOrRequestMFACode


class CustomAuthTokenLoginOrRequestMFACode(AuthTokenLoginOrRequestMFACode):
    """
    Class to handle throttling for login requests
    """
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'login'
