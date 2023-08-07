from requests import Response, Session
from rest_framework import status

LAUNCH_DARKLY_API_URL = "https://app.launchdarkly.com/api/v2"


class LaunchDarklyClient:
    def __init__(self, api_key: str):
        headers = {"Authorization": api_key}
        self.client = Session()
        self.client.headers = headers

    def get_project(self, project_id: str):
        response = self.client.get(f"{LAUNCH_DARKLY_API_URL}/projects/{project_id}")
        response_json = self._handle_response(response)
        return response_json

    def get_environments(self, project_id: str):
        response = self.client.get(
            f"{LAUNCH_DARKLY_API_URL}/projects/{project_id}/environments/"
        )
        response_json = self._handle_response(response)
        return response_json.get("items", [])

    def get_flags(self, project_id: str):
        response = self.client.get(f"{LAUNCH_DARKLY_API_URL}/flags/{project_id}")
        response_json = self._handle_response(response)
        return response_json.get("items", [])

    def _handle_response(self, response: Response):
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
