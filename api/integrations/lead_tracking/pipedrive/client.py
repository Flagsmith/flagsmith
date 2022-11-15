import typing

import requests

from integrations.lead_tracking.pipedrive.exceptions import PipedriveAPIError
from integrations.lead_tracking.pipedrive.models import (
    PipedriveLead,
    PipedriveOrganization,
    PipedriveOrganizationField,
)

PIPEDRIVE_BASE_URL = "https://flagsmith.pipedrive.com/api/v1"
ALLOWED_METHODS = ("get", "post", "put", "patch", "delete")


class PipedriveAPIClient:
    def __init__(self, api_token: str, base_url: str = PIPEDRIVE_BASE_URL):
        self.api_token = api_token
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def create_organization(self, organization: PipedriveOrganization):
        data = organization.to_request_data()
        api_response_data = self._make_request(
            resource="organizations",
            http_method="post",
            data=data,
            expected_status_code=201,
        )
        return PipedriveOrganization.from_response_data(api_response_data)

    def search_organizations(
        self, search_term: str
    ) -> typing.List[PipedriveOrganization]:
        api_response_data = self._make_request(
            resource="organizations/search",
            http_method="get",
            query_params={"term": search_term},
        )
        return [
            PipedriveOrganization.from_response_data(org["item"])
            for org in api_response_data["items"]
        ]

    def create_organization_field(
        self, organization_field: PipedriveOrganizationField
    ) -> PipedriveOrganizationField:
        data = organization_field.to_request_data()
        api_response_data = self._make_request(
            resource="organizationFields",
            http_method="post",
            data=data,
            expected_status_code=201,
        )
        return PipedriveOrganizationField.from_response_data(api_response_data)

    def get_organization_field(self, name: str) -> PipedriveOrganizationField:
        pass

    def create_lead(self, lead: PipedriveLead) -> PipedriveLead:
        data = lead.to_request_data()
        api_response_data = self._make_request(
            resource="leads",
            http_method="post",
            data=data,
            expected_status_code=201,
        )
        return PipedriveLead.from_response_data(api_response_data)

    def _make_request(
        self,
        resource: str,
        http_method: str,
        data: dict = None,
        query_params: dict = None,
        expected_status_code: int = 200,
    ) -> dict:
        http_method = http_method.lower()
        assert (
            http_method in ALLOWED_METHODS
        ), f"HTTP method must be one of {ALLOWED_METHODS}"
        request_method = getattr(self.session, http_method)
        url = f"{self.base_url}/{resource}?api_token={self.api_token}"
        response = request_method(url, json=data, params=query_params)
        if response.status_code != expected_status_code:
            raise PipedriveAPIError()
        return response.json()["data"]
