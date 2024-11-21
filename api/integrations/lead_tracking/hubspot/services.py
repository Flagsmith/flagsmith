import logging

from rest_framework.request import Request

from integrations.lead_tracking.hubspot.constants import HUBSPOT_COOKIE_NAME
from users.models import HubspotTracker

logger = logging.getLogger(__name__)


def register_hubspot_tracker(request: Request) -> None:
    hubspot_cookie = request.COOKIES.get(HUBSPOT_COOKIE_NAME)

    # TODO: Remove this temporary debugging logger statement.
    logger.info(f"Request cookies for user {request.user.email}: {request.COOKIES}")

    if hubspot_cookie:
        logger.info(
            f"Creating HubspotTracker instance for user {request.user.email} with cookie {hubspot_cookie}"
        )

        HubspotTracker.objects.update_or_create(
            user=request.user,
            defaults={
                "hubspot_cookie": hubspot_cookie,
            },
        )
    else:
        logger.info(
            f"Could not create HubspotTracker instance for user {request.user.email} since no cookie"
        )
