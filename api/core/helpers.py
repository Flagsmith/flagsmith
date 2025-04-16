import re
from typing import Any

from django.conf import settings
from django.contrib.sites import models as sites_models
from django.http import HttpRequest
from rest_framework.request import Request

INSECURE_DOMAINS = ("localhost", "127.0.0.1")

_insecure_domain_pattern = re.compile(rf"({'|'.join(INSECURE_DOMAINS)})(:\d+)?")


def get_current_site_url(request: HttpRequest | Request | None = None) -> str:
    if not (domain := settings.DOMAIN_OVERRIDE):
        try:
            domain = sites_models.Site.objects.get_current(request).domain
        except sites_models.Site.DoesNotExist:
            # For the rare case when `DOMAIN_OVERRIDE` was not set and no `Site` object present,
            # store a default domain `Site` in the sites cache
            # so it's correctly invalidated should the user decide to create own `Site` object.
            domain = settings.DEFAULT_DOMAIN
            sites_models.SITE_CACHE[settings.SITE_ID] = sites_models.Site(
                name="Flagsmith",
                domain=domain,
            )

    if request:
        scheme = request.scheme
    elif _insecure_domain_pattern.match(domain):
        scheme = "http"
    else:
        scheme = "https"

    return f"{scheme}://{domain}"


def get_ip_address_from_request(request: Request) -> Any | None:
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    return (
        x_forwarded_for.split(",")[0]
        if x_forwarded_for
        else request.META.get("REMOTE_ADDR")
    )
