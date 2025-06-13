import logging
import time
from typing import Any

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

    def create_user_hubspot_contact(self, user: FFAdminUser) -> str | None:
        tracker = HubspotTracker.objects.filter(user=user).first()
        tracker_cookie = tracker.hubspot_cookie if tracker else None
        self.client.create_lead_form(user=user, hubspot_cookie=tracker_cookie)

        # Create lead form creates a contact asynchronously in hubspot but does not return the contact id
        # We need to get the contact id separately and retry 3 times
        contact = None
        max_retries = 3
        for retry in range(max_retries + 1):
            contact = self.client.get_contact(user)
            if contact:
                break
            backoff = 0.5 * retry  # 3 retries: 0.5s, 1s, 1.5s
            time.sleep(backoff)
        if not contact:
            return None

        hubspot_contact_id: str = contact.get("id")

        # Hubspot creates contact asynchronously
        # If not available on the spot, following steps will sync database with Hubspot
        if hubspot_contact_id is not None:
            HubspotLead.objects.update_or_create(
                user=user, defaults={"hubspot_id": hubspot_contact_id}
            )

        return hubspot_contact_id

    def create_user_organisation_association(
        self, user: FFAdminUser, organisation: Organisation
    ) -> None:
        hubspot_contact_id = self._get_or_create_user_hubspot_id(user)
        if not hubspot_contact_id:
            return
        hubspot_org_id = self._get_or_create_organisation_hubspot_id(user, organisation)
        if not hubspot_org_id:
            return

        self.client.associate_contact_to_company(
            contact_id=hubspot_contact_id,
            company_id=hubspot_org_id,
        )

    def _get_or_create_user_hubspot_id(self, user: FFAdminUser) -> str | None:
        hubspot_lead = HubspotLead.objects.filter(user=user).first()
        if hubspot_lead:
            hubspot_contact_id: str | None = hubspot_lead.hubspot_id
        else:
            # Fallback to sync database with Hubspot if contact hubspot_id was not saved
            contact_data = self.client.get_contact(user)
            if contact_data:
                hubspot_contact_id = contact_data["id"]
                HubspotLead.objects.update_or_create(
                    user=user, defaults={"hubspot_id": hubspot_contact_id}
                )
            else:
                hubspot_contact_id = self.create_user_hubspot_contact(user)

        return hubspot_contact_id or None

    def _get_or_create_organisation_hubspot_id(
        self,
        user: FFAdminUser,
        organisation: Organisation,
    ) -> str | None:
        """
        Return the Hubspot API's id for an organisation.
        """
        if getattr(organisation, "hubspot_organisation", None):
            return organisation.hubspot_organisation.hubspot_id

        if user.email_domain in settings.HUBSPOT_IGNORE_ORGANISATION_DOMAINS:
            return None

        domain = user.email_domain
        company_kwargs = {"domain": domain}
        company_kwargs["name"] = organisation.name
        company_kwargs["organisation_id"] = organisation.id
        company_kwargs["active_subscription"] = organisation.subscription.plan

        # As Hubspot creates/associates companies based on contact domain
        # we need to get the hubspot id when this user creates the company for the first time
        # and update the company name
        company = self._get_or_create_hubspot_company(**company_kwargs)
        org_hubspot_id: str = company["id"]

        properties = company.get("properties", {})
        existing_name = properties.get("name")
        if existing_name != organisation.name:
            self.client.update_company(
                name=organisation.name,
                hubspot_company_id=org_hubspot_id,
            )

        # Store the organisation data in the database since we are
        # unable to look them up via a unique identifier.
        HubspotOrganisation.objects.create(
            organisation=organisation,
            hubspot_id=org_hubspot_id,
        )

        return org_hubspot_id

    def update_company_active_subscription(
        self, subscription: Subscription
    ) -> dict[str, Any] | None:
        if not subscription.plan:
            return None

        organisation = subscription.organisation

        # Check if we're missing the associated hubspot id.
        if not getattr(organisation, "hubspot_organisation", None):
            return None

        response: dict[str, Any] | None = self.client.update_company(
            active_subscription=subscription.plan,
            hubspot_company_id=organisation.hubspot_organisation.hubspot_id,
        )

        return response

    def _get_or_create_hubspot_company(
        self,
        domain: str,
        organisation_id: int,
        name: str,
        active_subscription: str | None = None,
    ) -> dict[str, Any]:
        company = self.client.get_company_by_domain(domain)
        if not company:
            company = self.client.create_company(
                name=name,
                domain=domain,
                organisation_id=organisation_id,
                active_subscription=active_subscription,
            )

        return company  # type: ignore[no-any-return]

    def _get_client(self) -> HubspotClient:
        return HubspotClient()
