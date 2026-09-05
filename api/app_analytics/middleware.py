import importlib
from typing import Callable

from common.core.utils import is_saas
from django.conf import settings
from django.http import HttpRequest, HttpResponse

from app_analytics.mappers import map_request_to_labels
from app_analytics.services import track_usage_by_resource_host_and_environment

from .track import (
    get_resource_from_uri,
    track_request_googleanalytics_async,
)


class GoogleAnalyticsMiddleware:
    def __init__(self, get_response):  # type: ignore[no-untyped-def]
        self.get_response = get_response

    def __call__(self, request):  # type: ignore[no-untyped-def]
        # for each API request, trigger a call to Google Analytics to track the request
        track_request_googleanalytics_async(request)

        response = self.get_response(request)

        return response


class APIUsageMiddleware:
    def __init__(
        self,
        get_response: Callable[[HttpRequest], HttpResponse],
    ) -> None:
        self.get_response = get_response
        # An Edge Proxy reports the requests it serves itself, so its own
        # requests to core must not also be counted here. The private
        # edge_proxy app decides what counts as the proxy's own: a verified
        # X-Proxy-Key whose grants cover the presented environment — bare
        # header presence is never trusted.
        self.is_valid_edge_proxy_request: Callable[[HttpRequest], bool] | None = None
        if settings.EDGE_PROXY_INSTALLED and not is_saas():
            # getattr, not a hard import: the installed edge_proxy app may
            # predate the helper — the proxy's fetches are then counted as
            # before.
            self.is_valid_edge_proxy_request = getattr(
                importlib.import_module("edge_proxy.authentication"),
                "is_valid_edge_proxy_request",
                None,
            )

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if (environment_key := request.headers.get("X-Environment-Key")) and not (
            self.is_valid_edge_proxy_request is not None
            and self.is_valid_edge_proxy_request(request)
        ):
            track_usage_by_resource_host_and_environment(
                resource=get_resource_from_uri(request.path),
                host=request.get_host(),
                environment_key=environment_key,
                labels=map_request_to_labels(request),
            )

        response = self.get_response(request)

        return response
