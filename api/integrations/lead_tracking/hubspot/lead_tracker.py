import logging
import time
from typing import Any

from django.conf import settings

from integrations.lead_tracking.lead_tracking import LeadTracker
from organisations.models import Organisation
from users.models import FFAdminUser, HubspotLead, HubspotTracker

from .client import HubspotClient
from .constants import HUBSPOT_FORM_ID_SAAS

logger = logging.getLogger(__name__)


class HubspotLeadTracker(LeadTracker):
    @staticmethod
    def should_track(user: FFAdminUser) -> bool:
        return settings.ENABLE_HUBSPOT_LEAD_TRACKING

    def create_user_hubspot_contact(self, user: FFAdminUser) -> str | None:
        tracker = HubspotTracker.objects.filter(user=user).first()
        create_lead_form_kwargs: dict[str, Any] = {
            "user": user,
            "form_id": HUBSPOT_FORM_ID_SAAS,
        }
        if tracker:
            create_lead_form_kwargs.update(
                hubspot_cookie=tracker.hubspot_cookie,
                utm_data=tracker.utm_data,
            )
        self.client.create_lead_form(**create_lead_form_kwargs)

        # Create lead form creates a contact asynchronously in hubspot but does not return the contact id
        # We need to get the contact id separately and retry 3 times
        contact = self._get_new_contact_with_retry(user, max_retries=3)
        if not contact:
            # Hubspot creates contact asynchronously
            # If not available on the spot, following steps will sync database with Hubspot
            logger.error(f"Failed to create contact for user {user.email}")
            return None

        hubspot_contact_id = contact.get("id")
        HubspotLead.objects.update_or_create(
            user=user, defaults={"hubspot_id": hubspot_contact_id}
        )

        return hubspot_contact_id

    def create_lead(self, user: FFAdminUser, organisation: Organisation) -> None:
        # Only create the contact. HubSpot handles company creation and
        # association automatically from the contact's email domain.
        self._get_or_create_user_hubspot_id(user)

    def _get_new_contact_with_retry(
        self, user: FFAdminUser, max_retries: int = 3
    ) -> dict[str, Any] | None:
        for retry in range(max_retries + 1):
            contact = self.client.get_contact(user)
            if contact:
                return contact  # type: ignore[no-any-return]
            time.sleep(0.5 * retry)  # 3 retries: 0.5s, 1s, 1.5s
        return None

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
                logger.error(
                    f"Fallback creating contact for user {user.email} when associating with organisation"
                )
                hubspot_contact_id = self.create_user_hubspot_contact(user)

        return hubspot_contact_id

    def _get_client(self) -> HubspotClient:
        return HubspotClient()
