import re

from django.conf import settings
from django.contrib.sites.models import Site
from django.http import HttpRequest
from rest_framework.request import Request

INSECURE_DOMAINS = ("localhost", "127.0.0.1")

_insecure_domain_pattern = re.compile(rf'({"|".join(INSECURE_DOMAINS)})(:\d+)?')


def get_current_site_url(request: HttpRequest | Request | None = None) -> str:
    if settings.DOMAIN_OVERRIDE:
        domain = settings.DOMAIN_OVERRIDE
    elif current_site := Site.objects.filter(id=settings.SITE_ID).first():
        domain = current_site.domain
    else:
        domain = settings.DEFAULT_DOMAIN

    if request:
        scheme = request.scheme
    elif _insecure_domain_pattern.match(domain):
        scheme = "http"
    else:
        scheme = "https"

    return f"{scheme}://{domain}"


def get_ip_address_from_request(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    return (
        x_forwarded_for.split(",")[0]
        if x_forwarded_for
        else request.META.get("REMOTE_ADDR")
    )
