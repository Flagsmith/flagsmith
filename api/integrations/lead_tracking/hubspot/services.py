import logging

from rest_framework.request import Request

from integrations.lead_tracking.hubspot.client import HubspotClient
from integrations.lead_tracking.hubspot.constants import (
    HUBSPOT_ACTIVE_SUBSCRIPTION_SELF_HOSTED,
    HUBSPOT_COOKIE_NAME,
)
from users.models import FFAdminUser, HubspotTracker

logger = logging.getLogger(__name__)


def register_hubspot_tracker(request: Request, user: FFAdminUser | None = None) -> None:
    hubspot_cookie = request.data.get(HUBSPOT_COOKIE_NAME)
    track_user = user if user else request.user
    if not hubspot_cookie:
        logger.info(f"Request did not included Hubspot data for user {track_user.id}")
        return

    if (
        HubspotTracker.objects.filter(hubspot_cookie=hubspot_cookie)  # type: ignore[misc]
        .exclude(user=track_user)
        .exists()
    ):
        logger.info(
            f"HubspotTracker could not be created for user {track_user.id}"
            f" due to cookie conflict with cookie {hubspot_cookie}"
        )
        return

    HubspotTracker.objects.update_or_create(
        user=track_user,
        defaults={
            "hubspot_cookie": hubspot_cookie,
        },
    )
    logger.info(
        f"Created HubspotTracker instance for user {track_user.id} with cookie {hubspot_cookie}"
    )


def create_self_hosted_onboarding_lead(
    email: str, first_name: str, last_name: str, organisation_name: str
) -> None:
    email_domain = email.split("@")[1]
    hubspot_client = HubspotClient()
    company = hubspot_client.get_company_by_domain(email_domain)
    if not company:
        company = hubspot_client.create_company(
            name=organisation_name,
            domain=email_domain,
            active_subscription=HUBSPOT_ACTIVE_SUBSCRIPTION_SELF_HOSTED,
        )

    company_id = company["id"]

    hubspot_client.create_self_hosted_contact(email, first_name, last_name, company_id)
