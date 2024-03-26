import logging

from django.conf import settings

from integrations.lead_tracking.lead_tracking import LeadTracker
from organisations.models import HubspotOrganisation, Organisation
from users.models import FFAdminUser

from .client import HubspotClient

logger = logging.getLogger(__name__)

try:
    import re2 as re

    logger.info("Using re2 library for regex.")
except ImportError:
    logger.warning("Unable to import re2. Falling back to re.")
    import re


class HubspotLeadTracker(LeadTracker):
    @staticmethod
    def should_track(user: FFAdminUser) -> bool:
        if not settings.ENABLE_HUBSPOT_LEAD_TRACKING:
            return False

        domain = user.email_domain

        if settings.HUBSPOT_IGNORE_DOMAINS_REGEX and re.match(
            settings.HUBSPOT_IGNORE_DOMAINS_REGEX, domain
        ):
            return False

        if (
            settings.HUBSPOT_IGNORE_DOMAINS
            and domain in settings.HUBSPOT_IGNORE_DOMAINS
        ):
            return False

        if any(
            org.is_paid
            for org in user.organisations.select_related("subscription").all()
        ):
            return False

        return True

    def create_lead(self, user: FFAdminUser, organisation: Organisation) -> None:
        contact_data = self.client.get_contact(user)

        if contact_data:
            # The user is already present in the system as a lead
            # for an existing organisation, so return early.
            return

        hubspot_id = self.get_or_create_organisation_hubspot_id(organisation)

        self.client.create_contact(user, hubspot_id)

    def get_or_create_organisation_hubspot_id(self, organisation: Organisation) -> str:
        """
        Return the Hubspot API's id for an organisation.
        """
        if getattr(organisation, "hubspot_organisation", None):
            return organisation.hubspot_organisation.hubspot_id

        response = self.client.create_company(
            name=organisation.name,
            organisation_id=organisation.id,
        )
        # Store the organisation data in the database since we are
        # unable to look them up via a unique identifier.
        HubspotOrganisation.objects.create(
            organisation=organisation,
            hubspot_id=response["id"],
        )
        return response["id"]

    def _get_client(self) -> HubspotClient:
        return HubspotClient()
