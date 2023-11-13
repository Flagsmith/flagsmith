from django.conf import settings
from django.contrib.sites.models import Site


def get_current_site_url():
    if settings.DOMAIN_OVERRIDE:
        domain = settings.DOMAIN_OVERRIDE
    elif current_site := Site.objects.filter(id=settings.SITE_ID).first():
        domain = current_site.domain
    else:
        domain = settings.DEFAULT_DOMAIN

    url = "https://" + domain
    return url


def get_ip_address_from_request(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    return (
        x_forwarded_for.split(",")[0]
        if x_forwarded_for
        else request.META.get("REMOTE_ADDR")
    )
