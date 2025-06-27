import json
import logging
from typing import TYPE_CHECKING, Any

import hubspot  # type: ignore[import-untyped]
import requests
from django.conf import settings
from hubspot.crm.associations.v4 import AssociationSpec  # type: ignore[import-untyped]
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
from users.models import HubspotTracker

if TYPE_CHECKING:
    from users.models import FFAdminUser

logger = logging.getLogger(__name__)


class HubspotClient:
    def __init__(self, client: hubspot.Client = None) -> None:
        self.access_token = settings.HUBSPOT_ACCESS_TOKEN
        self.client = client or hubspot.Client.create(access_token=self.access_token)

    def get_contact(self, user: "FFAdminUser") -> None | dict[str, Any]:
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
        self,
        user: "FFAdminUser",
        hubspot_cookie: str | None = None,
        utm_data: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        utm_data = utm_data or {}
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

        fields.extend(
            {"objectTypeId": "0-1", "name": k, "value": v} for k, v in utm_data.items()
        )

        context = {}
        if hubspot_cookie:
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

    def associate_contact_to_company(self, contact_id: str, company_id: str) -> None:
        association_spec = [
            AssociationSpec(
                association_category="HUBSPOT_DEFINED", association_type_id=1
            )
        ]

        self.client.crm.associations.v4.basic_api.create(
            object_type="contacts",
            object_id=contact_id,
            to_object_type="companies",
            to_object_id=company_id,
            association_spec=association_spec,
        )

    def create_self_hosted_contact(
        self, email: str, first_name: str, last_name: str, hubspot_company_id: str
    ) -> None:
        properties = {
            "email": email,
            "firstname": first_name,
            "lastname": last_name,
            "api_lead_source": HUBSPOT_API_LEAD_SOURCE_SELF_HOSTED,
        }

        create_params = {
            "simple_public_object_input_for_create": SimplePublicObjectInputForCreate(
                properties=properties,
            )
        }

        if hubspot_company_id:
            create_params["simple_public_object_input_for_create"].associations = [
                {
                    "types": [
                        {
                            "associationCategory": "HUBSPOT_DEFINED",
                            "associationTypeId": 1,
                        }
                    ],
                    "to": {"id": hubspot_company_id},
                }
            ]

        response = self.client.crm.contacts.basic_api.create(**create_params)
        return response.to_dict()  # type: ignore[no-any-return]

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
        self,
        hubspot_company_id: str,
        name: str | None = None,
        active_subscription: str | None = None,
    ) -> dict[str, Any]:
        properties = {}
        if name is not None:
            properties["name"] = name
        if active_subscription is not None:
            properties["active_subscription"] = active_subscription

        simple_public_object_input = SimplePublicObjectInput(properties=properties)

        response = self.client.crm.companies.basic_api.update(
            company_id=hubspot_company_id,
            simple_public_object_input=simple_public_object_input,
        )

        return response.to_dict()  # type: ignore[no-any-return]
