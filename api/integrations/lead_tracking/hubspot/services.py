import logging

from rest_framework.request import Request

from integrations.lead_tracking.hubspot.constants import HUBSPOT_COOKIE_NAME
from users.models import HubspotTracker

logger = logging.getLogger(__name__)


def register_hubspot_tracker(request: Request) -> None:
    hubspot_cookie = request.data.get(HUBSPOT_COOKIE_NAME)

    if not hubspot_cookie:
        logger.info(
            f"Request did not included Hubspot data for user {request.user.email}"
        )
        return

    logger.info(
        f"Creating HubspotTracker instance for user {request.user.email} with cookie {hubspot_cookie}"
    )

    HubspotTracker.objects.update_or_create(
        user=request.user,
        defaults={
            "hubspot_cookie": hubspot_cookie,
        },
    )
