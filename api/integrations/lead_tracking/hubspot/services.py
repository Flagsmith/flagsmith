from rest_framework.request import Request

from integrations.lead_tracking.hubspot.constants import HUBSPOT_COOKIE_NAME
from users.models import HubspotTracker


def register_hubspot_tracker(request: Request) -> None:
    hubspot_cookie = request.COOKIES.get(HUBSPOT_COOKIE_NAME)

    if hubspot_cookie:
        HubspotTracker.objects.update_or_create(
            user=request.user,
            defaults={
                "hubspot_cookie": hubspot_cookie,
            },
        )
