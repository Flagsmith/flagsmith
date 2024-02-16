import random
from pprint import pprint

import hubspot
from django.conf import settings
from hubspot.crm.companies import (
    ApiException,
    SimplePublicObjectInputForCreate,
)

from users.models import FFAdminUser

random_number = random.randint(0, 10000)


access_token = settings.HUBSPOT_ACCESS_TOKEN
client = hubspot.Client.create(access_token=access_token)


def create_contact(user: FFAdminUser) -> dict:
    properties = {
        "email": user.email,
        "firstname": user.first_name,
        "lastname": user.last_name,
    }

    # ZACH: TODO: load company ids from some sort of search
    #             interface / creating them as needed
    temp_company_id = "10117147860"
    response = client.crm.contacts.basic_api.create(
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
                    "to": {"id": temp_company_id},
                }
            ],
        )
    )

    pprint(response)

    return response


def create_company(name: str, domain: str) -> dict:
    properties = {
        "name": name,
        "domain": domain,
    }
    simple_public_object_input_for_create = SimplePublicObjectInputForCreate(
        properties=properties,
    )

    # ZACH: TODO: Use the ApiException class to add handlers for access to the api
    assert ApiException
    response = client.crm.companies.basic_api.create(
        simple_public_object_input_for_create=simple_public_object_input_for_create,
    )
    return response
