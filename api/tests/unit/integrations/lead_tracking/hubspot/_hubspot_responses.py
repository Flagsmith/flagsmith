from datetime import datetime

from dateutil.tz import tzlocal


class FakeHubspotResponse:
    """
    Dummy class to replicate the to_dict() method of the Hubspot response classes.
    """

    def __init__(self, data: dict) -> None:
        self.data = data

    def to_dict(self) -> dict:
        return self.data


def generate_get_company_by_domain_response(
    name: str, domain: str
) -> FakeHubspotResponse:
    """
    Generate a sample response given by the Hubspot API when searching for a company by domain.

    This response was retrieved from the API directly, and then modified to allow us to set the
    certain properties dynamically.
    """

    return FakeHubspotResponse(
        data={
            "paging": None,
            "results": [
                {
                    "archived": False,
                    "archived_at": None,
                    "created_at": datetime(
                        2024, 1, 25, 21, 48, 28, 655000, tzinfo=tzlocal()
                    ),
                    "id": "9765318341",
                    "properties": {
                        "createdate": "2024-01-25T21:48:28.655Z",
                        "domain": domain,
                        "hs_lastmodifieddate": "2024-04-23T15:54:13.336Z",
                        "hs_object_id": "9765318341",
                        "name": name,
                    },
                    "properties_with_history": None,
                    "updated_at": datetime(
                        2024, 4, 23, 15, 54, 13, 336000, tzinfo=tzlocal()
                    ),
                }
            ],
            "total": 1,
        }
    )


def generate_get_company_by_domain_response_no_results() -> FakeHubspotResponse:
    """
    Generate a sample response given by the Hubspot API when searching for a company by domain
    but no results are returned.

    This response was retrieved from the API directly and hard coded here for simplicity.
    """

    return FakeHubspotResponse(
        data={
            "paging": None,
            "results": [],
            "total": 0,
        }
    )


def generate_create_company_response(
    name: str, domain: str | None = None, organisation_id: None | int = None
) -> FakeHubspotResponse:
    """
    Generate a sample response given by the Hubspot API when creating a company.

    This response was retrieved from the API directly, and then modified to allow us to set the
    properties dynamically.
    """

    properties = {
        "active_subscription": None,
        "createdate": "2024-04-23T17:36:50.158Z",
        "domain": domain,
        "hs_lastmodifieddate": "2024-04-23T17:36:50.158Z",
        "hs_object_id": "11349198823",
        "hs_object_source": "INTEGRATION",
        "hs_object_source_id": "2902325",
        "hs_object_source_label": "INTEGRATION",
        "name": name,
        "website": domain,
    }

    if organisation_id:
        properties["orgid_unique"] = organisation_id

    return FakeHubspotResponse(
        data={
            "archived": False,
            "archived_at": None,
            "created_at": datetime(2024, 4, 23, 17, 36, 50, 158000, tzinfo=tzlocal()),
            "id": "11349198823",
            "properties": properties,
            "properties_with_history": None,
            "updated_at": datetime(2024, 4, 23, 17, 36, 50, 158000, tzinfo=tzlocal()),
        }
    )
