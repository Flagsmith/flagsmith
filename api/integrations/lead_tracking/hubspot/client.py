import json
import logging
from typing import Any

import hubspot  # type: ignore[import-untyped]
import requests
from django.conf import settings
from hubspot.crm.companies import (  # type: ignore[import-untyped]
    PublicObjectSearchRequest,
    SimplePublicObjectInput,
    SimplePublicObjectInputForCreate,
)
from hubspot.crm.contacts import (  # type: ignore[import-untyped]
    BatchReadInputSimplePublicObjectId,
)

from integrations.lead_tracking.hubspot.constants import (
    HUBSPOT_API_LEAD_SOURCE_SELF_HOSTED,
    HUBSPOT_FORM_ID,
    HUBSPOT_PORTAL_ID,
    HUBSPOT_ROOT_FORM_URL,
)
from users.models import FFAdminUser

logger = logging.getLogger(__name__)


class HubspotClient:
    def __init__(self, client: hubspot.Client = None) -> None:
        self.access_token = settings.HUBSPOT_ACCESS_TOKEN
        self.client = client or hubspot.Client.create(access_token=self.access_token)

    def get_contact(self, user: FFAdminUser) -> None | dict[str, Any]:
        public_object_id = BatchReadInputSimplePublicObjectId(
            id_property="email",
            inputs=[{"id": user.email}],
            properties=["email", "firstname", "lastname"],
        )

        response = self.client.crm.contacts.batch_api.read(
            batch_read_input_simple_public_object_id=public_object_id,
            archived=False,
        )

        results = response.to_dict()["results"]
        if not results:
            return None

        if len(results) > 1:
            logger.warning(
                "Hubspot contact endpoint is non-unique which should not be possible"
            )

        return results[0]  # type: ignore[no-any-return]

    def create_lead_form(
        self, user: FFAdminUser, hubspot_cookie: str
    ) -> dict[str, Any]:
        logger.info(
            f"Creating Hubspot lead form for user {user.email} with hubspot cookie {hubspot_cookie}"
        )
        fields = [
            {
                "objectTypeId": "0-1",
                "name": "email",
                "value": user.email,
            },
            {"objectTypeId": "0-1", "name": "firstname", "value": user.first_name},
            {"objectTypeId": "0-1", "name": "lastname", "value": user.last_name},
        ]

        context = {
            "hutk": hubspot_cookie,
            "pageUri": "www.flagsmith.com",
            "pageName": "Homepage",
        }

        legal = {
            "consent": {
                "consentToProcess": True,
                "text": "I agree to allow Flagsmith to store and process my personal data.",
                "communications": [
                    {
                        "value": user.marketing_consent_given,
                        "subscriptionTypeId": 999,
                        "text": "I agree to receive marketing communications from Flagsmith.",
                    }
                ],
            }
        }
        payload = {"legalConsentOptions": legal, "context": context, "fields": fields}
        headers = {
            "Content-Type": "application/json",
        }
        url = f"{HUBSPOT_ROOT_FORM_URL}/{HUBSPOT_PORTAL_ID}/{HUBSPOT_FORM_ID}"

        response = requests.post(url, headers=headers, data=json.dumps(payload))

        if response.status_code not in {200, 201}:
            logger.error(
                f"Problem posting data to Hubspot's form API due to {response.status_code} "
                f"status code and following response: {response.text}"
            )
        return response.json()  # type: ignore[no-any-return]

    def create_contact(
        self, user: FFAdminUser, hubspot_company_id: str
    ) -> dict[str, Any]:
        properties = {
            "email": user.email,
            "firstname": user.first_name,
            "lastname": user.last_name,
            "hs_marketable_status": user.marketing_consent_given,
        }
        return self._create_contact(properties, hubspot_company_id)

    def _create_contact(
        self, properties: dict[str, Any], hubspot_company_id: str
    ) -> dict[str, str]:
        response = self.client.crm.contacts.basic_api.create(
            simple_public_object_input_for_create=SimplePublicObjectInputForCreate(
                properties=properties,
                associations=[
                    {
                        "types": [
                            {
                                "associationCategory": "HUBSPOT_DEFINED",
                                "associationTypeId": 1,
                            }
                        ],
                        "to": {"id": hubspot_company_id},
                    }
                ],
            )
        )
        return response.to_dict()  # type: ignore[no-any-return]

    def create_self_hosted_contact(
        self, email: str, first_name: str, last_name: str, hubspot_company_id: str
    ) -> None:
        properties = {
            "email": email,
            "firstname": first_name,
            "lastname": last_name,
            "api_lead_source": HUBSPOT_API_LEAD_SOURCE_SELF_HOSTED,
        }
        self._create_contact(properties, hubspot_company_id)

    def get_company_by_domain(self, domain: str) -> dict[str, Any] | None:
        """
        Domain should be unique in Hubspot by design, so we should only ever have
        0 or 1 results.
        """
        public_object_search_request = PublicObjectSearchRequest(
            filter_groups=[
                {
                    "filters": [
                        {"value": domain, "propertyName": "domain", "operator": "EQ"}
                    ]
                }
            ]
        )

        response = self.client.crm.companies.search_api.do_search(
            public_object_search_request=public_object_search_request,
        )

        results = response.to_dict()["results"]
        if not results:
            return None

        if len(results) > 1:
            logger.error("Multiple companies exist in Hubspot for domain %s.", domain)

        return results[0]  # type: ignore[no-any-return]

    def create_company(
        self,
        name: str,
        active_subscription: str = None,  # type: ignore[assignment]
        organisation_id: int = None,  # type: ignore[assignment]
        domain: str | None = None,
    ) -> dict[str, Any]:
        properties = {"name": name}

        if domain:
            properties["domain"] = domain
        if active_subscription:
            properties["active_subscription"] = active_subscription
        if organisation_id:
            properties["orgid_unique"] = organisation_id  # type: ignore[assignment]

        simple_public_object_input_for_create = SimplePublicObjectInputForCreate(
            properties=properties,
        )

        response = self.client.crm.companies.basic_api.create(
            simple_public_object_input_for_create=simple_public_object_input_for_create,
        )

        return response.to_dict()  # type: ignore[no-any-return]

    def update_company(
        self, active_subscription: str, hubspot_company_id: str
    ) -> dict[str, Any]:
        properties = {
            "active_subscription": active_subscription,
        }
        simple_public_object_input = SimplePublicObjectInput(properties=properties)

        response = self.client.crm.companies.basic_api.update(
            company_id=hubspot_company_id,
            simple_public_object_input=simple_public_object_input,
        )

        return response.to_dict()  # type: ignore[no-any-return]
