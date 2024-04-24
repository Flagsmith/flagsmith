import logging

from django.conf import settings

from integrations.lead_tracking.lead_tracking import LeadTracker
from organisations.models import (
    HubspotOrganisation,
    Organisation,
    Subscription,
)
from users.models import FFAdminUser, HubspotLead

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

    def create_lead(self, user: FFAdminUser, organisation: Organisation = None) -> None:
        contact_data = self.client.get_contact(user)

        if contact_data:
            # The user is already present in the system as a lead
            # for an existing organisation, so return early.
            return

        hubspot_id = self.get_or_create_organisation_hubspot_id(user, organisation)

        response = self.client.create_contact(user, hubspot_id)

        HubspotLead.objects.create(user=user, hubspot_id=response["id"])

    def get_or_create_organisation_hubspot_id(
        self, user: FFAdminUser, organisation: Organisation = None
    ) -> str:
        """
        Return the Hubspot API's id for an organisation.
        """
        if organisation and getattr(organisation, "hubspot_organisation", None):
            return organisation.hubspot_organisation.hubspot_id

        if user.email_domain in settings.HUBSPOT_IGNORE_ORGANISATION_DOMAINS:
            domain = None
        else:
            domain = user.email_domain

        if organisation:
            response = self.client.create_company(
                name=organisation.name,
                active_subscription=organisation.subscription.plan,
                organisation_id=organisation.id,
                domain=domain,
            )

            # Store the organisation data in the database since we are
            # unable to look them up via a unique identifier.
            HubspotOrganisation.objects.create(
                organisation=organisation,
                hubspot_id=response["id"],
            )
        else:
            response = self._get_or_create_company_by_domain(domain)

        return response["id"]

    def update_company_active_subscription(
        self, subscription: Subscription
    ) -> dict | None:
        if not subscription.plan:
            return

        organisation = subscription.organisation

        # Check if we're missing the associated hubspot id.
        if not getattr(organisation, "hubspot_organisation", None):
            return

        response = self.client.update_company(
            active_subscription=subscription.plan,
            hubspot_company_id=organisation.hubspot_organisation.hubspot_id,
        )

        return response

    def _get_or_create_company_by_domain(self, domain: str) -> dict:
        company = self.client.get_company_by_domain(domain)
        if not company:
            company = self.client.create_company(name=domain)

        return company

    def _get_client(self) -> HubspotClient:
        return HubspotClient()
