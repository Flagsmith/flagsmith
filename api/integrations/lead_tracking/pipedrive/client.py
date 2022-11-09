import requests

from integrations.lead_tracking.pipedrive.exceptions import PipedriveAPIError
from integrations.lead_tracking.pipedrive.models import (
    PipedriveLead,
    PipedriveOrganization,
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
        data: dict,
        expected_status_code: int = 200,
    ) -> dict:
        http_method = http_method.lower()
        assert (
            http_method in ALLOWED_METHODS
        ), f"HTTP method must be one of {ALLOWED_METHODS}"
        request_method = getattr(self.session, http_method)
        url = f"{self.base_url}/{resource}?api_token={self.api_token}"
        response = request_method(url, json=data)
        if response.status_code != expected_status_code:
            raise PipedriveAPIError()
        return response.json()["data"]
