import typing

import requests

from integrations.lead_tracking.pipedrive.exceptions import PipedriveAPIError
from integrations.lead_tracking.pipedrive.models import (
    PipedriveDealField,
    PipedriveLead,
    PipedriveLeadLabel,
    PipedriveOrganization,
    PipedriveOrganizationField,
    PipedrivePerson,
)


class PipedriveAPIClient:
    def __init__(
        self,
        api_token: str,
        base_url: str,
        session: typing.Optional[requests.Session] = None,
    ):
        self.api_token = api_token
        self.base_url = base_url
        self.session = session or requests.Session()

    def create_organization(
        self, name: str, organization_fields: typing.Dict[str, typing.Any] = None
    ):
        api_response_data = self._make_request(
            resource="organizations",
            http_method="post",
            data={"name": name, **(organization_fields or {})},
            expected_status_code=201,
        )
        return PipedriveOrganization.from_response_data(api_response_data)

    def search_organizations(
        self, search_term: str
    ) -> typing.List[PipedriveOrganization]:
        api_response_data = self._make_request(
            resource="organizations/search",
            http_method="get",
            query_params={"term": search_term, "fields": "custom_fields"},
        )
        return [
            PipedriveOrganization.from_response_data(org["item"])
            for org in api_response_data["items"]
        ]

    def search_persons(self, search_term: str) -> typing.List[PipedrivePerson]:
        api_response_data = self._make_request(
            resource="persons/search",
            http_method="get",
            query_params={"term": search_term},
        )
        return [
            PipedrivePerson.from_response_data(person["item"])
            for person in api_response_data["items"]
        ]

    def create_organization_field(
        self, name: str, field_type: str = "varchar"
    ) -> PipedriveOrganizationField:
        api_response_data = self._make_request(
            resource="organizationFields",
            http_method="post",
            data={"name": name, "field_type": field_type},
            expected_status_code=201,
        )
        return PipedriveOrganizationField.from_response_data(api_response_data)

    def create_deal_field(
        self, name: str, field_type: str = "varchar"
    ) -> PipedriveDealField:
        api_response_data = self._make_request(
            resource="dealFields",
            http_method="post",
            data={"name": name, "field_type": field_type},
            expected_status_code=201,
        )
        return PipedriveDealField.from_response_data(api_response_data)

    def create_lead(
        self,
        title: str,
        organization_id: int,
        person_id: int = None,
        custom_fields: typing.Dict[str, typing.Any] = None,
        label_ids: typing.List[str] = None,
    ) -> PipedriveLead:
        data = {
            "title": title,
            "organization_id": organization_id,
            "label_ids": label_ids or [],
            **(custom_fields or {}),
        }
        if person_id:
            data["person_id"] = person_id

        api_response_data = self._make_request(
            resource="leads", http_method="post", data=data, expected_status_code=201
        )
        return PipedriveLead.from_response_data(api_response_data)

    def create_person(self, name: str, email: str) -> PipedrivePerson:
        api_response_data = self._make_request(
            resource="persons",
            http_method="post",
            data={
                "name": name,
                "email": email,
            },
            expected_status_code=201,
        )
        return PipedrivePerson.from_response_data(api_response_data)

    def list_lead_labels(self) -> typing.List[PipedriveLeadLabel]:
        api_response_data = self._make_request(
            resource="leadLabels",
            http_method="get",
            expected_status_code=200,
        )
        return [
            PipedriveLeadLabel.from_response_data(label) for label in api_response_data
        ]

    def _make_request(
        self,
        resource: str,
        http_method: str,
        data: dict = None,
        query_params: dict = None,
        expected_status_code: int = 200,
    ) -> dict:
        http_method = http_method.lower()
        if not hasattr(self.session, http_method):
            raise ValueError("`http_method` argument must be valid HTTP verb")
        request_method = getattr(self.session, http_method)
        url = f"{self.base_url}/{resource}?api_token={self.api_token}"

        try:
            response = request_method(url, json=data, params=query_params)
        except requests.exceptions.RequestException:
            raise PipedriveAPIError(
                "Unexpected error communicating with Pipedrive API."
            )

        if response.status_code != expected_status_code:
            raise PipedriveAPIError(
                f"Response code was {response.status_code}. Expected {expected_status_code}"
            )

        return response.json()["data"]
