import logging

import hubspot
from django.conf import settings
from hubspot.crm.companies import SimplePublicObjectInputForCreate
from hubspot.crm.contacts import BatchReadInputSimplePublicObjectId

from users.models import FFAdminUser

logger = logging.getLogger(__name__)


class HubspotClient:
    def __init__(self) -> None:
        access_token = settings.HUBSPOT_ACCESS_TOKEN
        self.client = hubspot.Client.create(access_token=access_token)

    def get_contact(self, user: FFAdminUser) -> None | dict:
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

        return results[0]

    def create_contact(self, user: FFAdminUser, hubspot_company_id: str) -> dict:
        properties = {
            "email": user.email,
            "firstname": user.first_name,
            "lastname": user.last_name,
            "hs_marketable_status": user.marketing_consent_given,
        }

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
        return response.to_dict()

    def create_company(self, name: str) -> dict:
        properties = {"name": name}
        simple_public_object_input_for_create = SimplePublicObjectInputForCreate(
            properties=properties,
        )

        response = self.client.crm.companies.basic_api.create(
            simple_public_object_input_for_create=simple_public_object_input_for_create,
        )

        return response.to_dict()
