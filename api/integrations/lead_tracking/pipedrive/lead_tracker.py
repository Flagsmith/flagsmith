import logging

from django.conf import settings

from integrations.lead_tracking.lead_tracking import LeadTracker
from users.models import FFAdminUser

from .client import PipedriveAPIClient
from .exceptions import EntityNotFoundError, MultipleMatchingOrganizationsError
from .models import PipedriveLead, PipedriveOrganization

logger = logging.getLogger(__name__)

try:
    import re2 as re

    logger.info("Using re2 library for regex.")
except ImportError:
    logger.warning("Unable to import re2. Falling back to re.")
    import re


class PipedriveLeadTracker(LeadTracker):
    @staticmethod
    def should_track(user: FFAdminUser):
        if not settings.ENABLE_PIPEDRIVE_LEAD_TRACKING:
            return False

        domain = user.email_domain

        if settings.PIPEDRIVE_IGNORE_DOMAINS_REGEX and re.match(
            settings.PIPEDRIVE_IGNORE_DOMAINS_REGEX, domain
        ):
            return False

        if (
            settings.PIPEDRIVE_IGNORE_DOMAINS
            and domain in settings.PIPEDRIVE_IGNORE_DOMAINS
        ):
            return False

        if any(
            org.is_paid
            for org in user.organisations.select_related("subscription").all()
        ):
            return False

        return True

    def create_lead(self, user: FFAdminUser) -> PipedriveLead:
        email_domain = user.email.split("@")[-1]

        try:
            organization = self._get_org_by_domain(email_domain)
        except EntityNotFoundError:
            organization = self.create_organization(email_domain)
        except MultipleMatchingOrganizationsError as e:
            logger.error(
                "Multiple organizations found in Pipedrive for domain %s", email_domain
            )
            raise e

        create_lead_kwargs = {
            "title": user.email,
            "organization_id": organization.id,
            "custom_fields": {},
        }
        if user.sign_up_type:
            create_lead_kwargs["custom_fields"][
                settings.PIPEDRIVE_SIGN_UP_TYPE_DEAL_FIELD_KEY
            ] = user.sign_up_type

        return self.client.create_lead(**create_lead_kwargs)

    def create_organization(self, organization_domain: str) -> PipedriveOrganization:
        org_name = PipedriveOrganization.get_org_name_from_domain(organization_domain)
        organization = self.client.create_organization(
            name=org_name,
            organization_fields={
                settings.PIPEDRIVE_DOMAIN_ORGANIZATION_FIELD_KEY: organization_domain
            },
        )
        return organization

    def _get_org_by_domain(self, domain: str) -> PipedriveOrganization:
        matching_organizations = self.client.search_organizations(domain)
        if not matching_organizations:
            raise EntityNotFoundError()
        elif len(matching_organizations) > 1:
            raise MultipleMatchingOrganizationsError()
        return matching_organizations[0]

    def _get_client(self) -> PipedriveAPIClient:
        return PipedriveAPIClient(
            api_token=settings.PIPEDRIVE_API_TOKEN,
            base_url=settings.PIPEDRIVE_BASE_API_URL,
        )
