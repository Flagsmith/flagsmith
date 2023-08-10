from requests import Response, Session
from rest_framework import status

LAUNCH_DARKLY_API_URL = "https://app.launchdarkly.com/api/v2"


class LaunchDarklyClient:
    def __init__(self, api_key: str):
        headers = {"Authorization": api_key}
        self.client = Session()
        self.client.headers = headers

    def get_project(self, project_id: str) -> dict:
        endpoint = f"{LAUNCH_DARKLY_API_URL}/projects/{project_id}"
        return self._get_json_response(endpoint)

    def get_environments(self, project_id: str) -> list:
        endpoint = f"{LAUNCH_DARKLY_API_URL}/projects/{project_id}/environments/"
        response_data = self._get_json_response(endpoint)
        return response_data.get("items", [])

    def get_flags(self, project_id: str) -> list:
        endpoint = f"{LAUNCH_DARKLY_API_URL}/flags/{project_id}"
        response_data = self._get_json_response(endpoint)
        return response_data.get("items", [])

    def _get_json_response(self, endpoint: str) -> dict:
        response = self.client.get(endpoint)
        response.raise_for_status()
        return response.json()

    def _handle_response(self, response: Response) -> dict:
        match response.status_code:
            case status.HTTP_400_BAD_REQUEST:
                pass
            case status.HTTP_401_UNAUTHORIZED:
                pass
            case status.HTTP_403_FORBIDDEN:
                pass
            case status.HTTP_404_NOT_FOUND:
                pass
            case status.HTTP_429_TOO_MANY_REQUESTS:
                pass
            case _:
                return response.json()
