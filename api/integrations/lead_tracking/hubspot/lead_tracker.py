import logging

from django.conf import settings

from integrations.lead_tracking.lead_tracking import LeadTracker
from organisations.models import (
    HubspotOrganisation,
    Organisation,
    Subscription,
)
from users.models import FFAdminUser, HubspotLead, HubspotTracker

from .client import HubspotClient

logger = logging.getLogger(__name__)

try:
    import re2 as re  # type: ignore[import-untyped]

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

        return True

    def create_user_hubspot_contact(self, user: FFAdminUser) -> str:
        tracker = HubspotTracker.objects.filter(user=user).first()
        tracker_cookie = tracker.hubspot_cookie if tracker else None
        self.client.create_lead_form(user=user, hubspot_cookie=tracker_cookie)

        contact = self.client.get_contact(user)
        hubspot_id: str = contact["id"]

        HubspotLead.objects.update_or_create(
            user=user, defaults={"hubspot_id": hubspot_id}
        )

        return hubspot_id

    def create_organisation_lead(
        self, user: FFAdminUser, organisation: Organisation | None = None
    ) -> None:
        print("plop3")
        hubspot_contact_id = self.get_or_create_user_hubspot_id(user)
        hubspot_org_id = self.get_or_create_organisation_hubspot_id(user, organisation)
        self.client.associate_contact_to_company(
            contact_id=hubspot_contact_id,
            company_id=hubspot_org_id,
        )

    def get_or_create_user_hubspot_id(self, user: FFAdminUser) -> str:
        hubspot_lead = HubspotLead.objects.filter(user=user).first()
        if hubspot_lead:
            hubspot_contact_id = hubspot_lead.hubspot_id
        else:
            contact_data = self.client.get_contact(user)
            if contact_data:
                hubspot_contact_id = contact_data["id"]
            else:
                hubspot_contact_id = self.create_user_hubspot_contact(user)

        return hubspot_contact_id

    def get_or_create_organisation_hubspot_id(
        self,
        user: FFAdminUser,
        organisation: Organisation | None = None,
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

        org_hubspot_id: str = response["id"]
        return org_hubspot_id

    def update_company_active_subscription(
        self, subscription: Subscription
    ) -> dict | None:  # type: ignore[type-arg]
        if not subscription.plan:
            return  # type: ignore[return-value]

        organisation = subscription.organisation

        # Check if we're missing the associated hubspot id.
        if not getattr(organisation, "hubspot_organisation", None):
            return  # type: ignore[return-value]

        response = self.client.update_company(
            active_subscription=subscription.plan,
            hubspot_company_id=organisation.hubspot_organisation.hubspot_id,
        )

        return response  # type: ignore[no-any-return]

    def _get_or_create_company_by_domain(self, domain: str) -> dict:  # type: ignore[type-arg]
        company = self.client.get_company_by_domain(domain)
        if not company:
            # Since we don't know the company's name, we pass the domain as
            # both the name and the domain. This can then be manually
            # updated in Hubspot if needed.
            company = self.client.create_company(name=domain, domain=domain)

        return company  # type: ignore[no-any-return]

    def _get_client(self) -> HubspotClient:
        return HubspotClient()
