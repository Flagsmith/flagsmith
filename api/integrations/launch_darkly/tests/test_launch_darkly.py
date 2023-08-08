import json
import os
from unittest.mock import MagicMock

import pytest

from integrations.launch_darkly.client import LaunchDarklyClient
from integrations.launch_darkly.launch_darkly import LaunchDarklyWrapper
from integrations.launch_darkly.serializers import LaunchDarklyImportSerializer


@pytest.mark.parametrize(
    "ld_project_response, ld_env_response, ld_flags_response",
    [
        (
            "standard_project_response.json",
            "standard_environments_response",
            "standard_flags_response.json",
        )
    ],
)
def test_launch_darkly_import_into_new_project(
    ld_project_response, ld_env_response, ld_flags_response, organisation
):
    # Given
    ld_client_mock = _build_launch_darkly_client_mock(
        ld_project_response, ld_env_response, ld_flags_response
    )
    data = {
        "project_id": "",
        "organisation_id": organisation.id,
        "ld_project_id": "another-project",
    }
    serializer = LaunchDarklyImportSerializer(data=data)

    # When
    LaunchDarklyWrapper(
        client=ld_client_mock, request=serializer, api_key=None, user=None
    ).import_data()

    # Then
    assert False


def _build_launch_darkly_client_mock(
    ld_project_response, ld_env_response, ld_flags_response
):
    project_response = _read_json_file(ld_project_response)
    env_response = _read_json_file(ld_env_response)
    flags_response = _read_json_file(ld_flags_response)

    ld_client_mock = MagicMock(spec=LaunchDarklyClient)
    ld_client_mock.get_project.return_value = project_response
    ld_client_mock.get_environments.return_value = env_response
    ld_client_mock.get_flags.return_value = flags_response

    return ld_client_mock


def _read_json_file(file_path):
    script_directory = os.path.dirname(os.path.abspath(__file__))
    absolute_file_path = os.path.join(script_directory, file_path)

    if not os.path.exists(absolute_file_path):
        return None

    with open(absolute_file_path, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data
