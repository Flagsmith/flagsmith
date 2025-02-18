from typing import Any
from urllib.parse import urlparse

from core.helpers import get_current_site_url
from corsheaders.signals import check_request_enabled  # type: ignore[import-untyped]
from django.dispatch import receiver
from django.http import HttpRequest


@receiver(check_request_enabled)
def cors_allow_current_site(request: HttpRequest, **kwargs: Any) -> bool:
    # The signal is expected to only be dispatched:
    # - When `settings.CORS_ORIGIN_ALLOW_ALL` is set to `False`.
    # - For requests with `HTTP_ORIGIN` set.
    origin_url = urlparse(request.META["HTTP_ORIGIN"])
    current_site_url = urlparse(get_current_site_url(request))
    return (  # type: ignore[no-any-return]
        origin_url.scheme == current_site_url.scheme
        and origin_url.netloc == current_site_url.netloc
    )
