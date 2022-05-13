from django.conf import settings
from django.contrib.sites.models import Site


def get_current_site_url(default_domain: str = "app.flagsmith.com"):
    current_site = Site.objects.filter(id=settings.SITE_ID).first()

    url = "https://"
    url += current_site.domain if current_site else "app.flagsmith.com"
    return url


def get_ip_address_from_request(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    return (
        x_forwarded_for.split(",")[0]
        if x_forwarded_for
        else request.META.get("REMOTE_ADDR")
    )
