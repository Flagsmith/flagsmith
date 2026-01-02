from django.views import View
from rest_framework.request import Request
from rest_framework.throttling import SimpleRateThrottle


class InfluxQueryThrottle(SimpleRateThrottle):
    scope = "influx_query"

    def get_cache_key(self, request: Request, view: View) -> str:
        """
        Since we want to throttle requests across multiple views and viewsets that don't
        necessarily have the option to define the scope themselves, we override the
        get_cache_key method to ensure that the throttling logic behaves as expected.
        """
        if request.user and request.user.is_authenticated:
            return self.cache_format % {
                "scope": self.scope,
                "ident": request.user.pk,
            }
        return self.cache_format % {  # pragma: no cover
            "scope": self.scope,
            "ident": self.get_ident(request),
        }
