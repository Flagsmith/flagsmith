from requests import Response, Session
from rest_framework import status

LAUNCH_DARKLY_API_URL = "https://app.launchdarkly.com/api/v2"


class LaunchDarklyWrapper:
    def __init__(self, api_key: str):
        self.headers = {"Authorization": api_key}
        self.client = Session()

    def import_data(self, project_id: str):
        project = self._get_project(project_id)
        environments = self._get_environments(project_id)
        flags = self._get_flags(project_id)

    def _get_project(self, project_id):
        response = self.client.get(
            f"{LAUNCH_DARKLY_API_URL}/projects/{project_id}", headers=self.headers
        )
        response_json = self._handle_response(response)
        return response_json.get("items", [])

    def _get_environments(self, project_id: str):
        response = self.client.get(
            f"{LAUNCH_DARKLY_API_URL}/projects/{project_id}/environments/", headers=self.headers
        )
        response_json = self._handle_response(response)
        return response_json.get("items", [])

    def _get_flags(self, project_id):
        response = self.client.get(
            f"{LAUNCH_DARKLY_API_URL}/flags/{project_id}", headers=self.headers
        )
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


