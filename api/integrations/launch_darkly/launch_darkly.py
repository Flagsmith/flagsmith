from uuid import UUID

from requests import Response, Session
from rest_framework import status

from environments.models import Environment
from integrations.launch_darkly.serializers import LaunchDarklyImportSerializer
from organisations.models import Organisation
from projects.models import Project

LAUNCH_DARKLY_API_URL = "https://app.launchdarkly.com/api/v2"


class LaunchDarklyWrapper:
    def __init__(self, api_key: str):
        headers = {"Authorization": api_key}
        self.client = Session()
        self.client.headers = headers

    def import_data(self, request: LaunchDarklyImportSerializer):
        organisation = Organisation.objects.get(pk=request["organisation_id"])

        try:
            project_id = request["project_id"]
            project = Project.objects.get(project_id)
        except KeyError:
            ld_project = self._get_project(request["ld_project_id"])
            project = self._create_project(organisation, ld_project)

        ld_environments = self._get_environments(request["ld_project_id"])
        ld_flags = self._get_flags(request["ld_project_id"])

        environments = []
        for ld_environment in ld_environments:
            environment = self._create_environment(ld_environment, project)
            environments.append(environment)

        for ld_flag in ld_flags:
            feature = self._create_feature(ld_flag, environments)

    def _get_project(self, project_id: str):
        response = self.client.get(
            f"{LAUNCH_DARKLY_API_URL}/projects/{project_id}"
        )
        response_json = self._handle_response(response)
        return response_json

    def _get_environments(self, project_id: str):
        response = self.client.get(
            f"{LAUNCH_DARKLY_API_URL}/projects/{project_id}/environments/"
        )
        response_json = self._handle_response(response)
        return response_json.get("items", [])

    def _get_flags(self, project_id: str):
        response = self.client.get(
            f"{LAUNCH_DARKLY_API_URL}/flags/{project_id}"
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

    def _create_project(self, organisation_id: UUID, ld_project: dict) -> Project:
        return Project.objects.create(
            organisation_id=organisation_id,
            name=ld_project.get("name")
        )

    def _create_environment(self, ld_environment, project: Project) -> Environment:
        return Environment.objects.create(
            name=ld_environment.get("name"),
            project=project,

        )

    def _create_feature(self, ld_flag, environments: list[Environment]):
        match ld_flag.get("kind"):
            case "boolean":
                self._create_boolean_feature(ld_flag, environments)
            case "multivariate":
                self._create_multivariate_feature(ld_flag, environments)
            case _:
                raise Exception("Invalid flag type from Launch Darkly")

    def _create_boolean_feature(self, ld_flag, environments: list[Environment]):
        pass

    def _create_multivariate_feature(self, ld_flag, environments: list[Environment]):
        pass