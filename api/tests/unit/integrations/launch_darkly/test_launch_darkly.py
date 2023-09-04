import json
import os
from unittest.mock import MagicMock

import pytest

from environments.models import Environment
from features.models import Feature, FeatureStateValue
from features.multivariate.models import (
    MultivariateFeatureOption,
    MultivariateFeatureStateValue,
)
from integrations.launch_darkly.client import LaunchDarklyClient
from integrations.launch_darkly.enums import LogLevel
from integrations.launch_darkly.launch_darkly import LaunchDarklyWrapper
from integrations.launch_darkly.models import LaunchDarklyImportLog
from integrations.launch_darkly.serializers import LaunchDarklyImportSerializer
from projects.models import Project


@pytest.mark.parametrize(
    "ld_project_response, ld_env_response, ld_flags_response",
    [
        (
            "./data/standard_project_response.json",
            "./data/standard_environments_response.json",
            "./data/standard_flags_response.json",
        )
    ],
)
def test_launch_darkly_import_into_new_project(
    ld_project_response, ld_env_response, ld_flags_response, organisation, test_user
):
    # Given
    ld_client_mock = _build_launch_darkly_client_mock(
        ld_project_response, ld_env_response, ld_flags_response
    )
    data = {
        "api_key": "test-api-key",
        "project_id": None,
        "organisation_id": organisation.id,
        "ld_project_id": "another-project",
    }
    serializer = LaunchDarklyImportSerializer(data=data)
    serializer.is_valid()

    # When
    response = LaunchDarklyWrapper(
        client=ld_client_mock, request=serializer, user=test_user
    ).import_data()

    # Then
    assert response.completed_at
    assert (
        LaunchDarklyImportLog.objects.filter(
            launch_darkly_import=response, log_level=LogLevel.ERROR
        ).count()
        == 0
    )
    assert (
        LaunchDarklyImportLog.objects.filter(
            launch_darkly_import=response, log_level=LogLevel.CRITICAL
        ).count()
        == 0
    )

    # And
    assert Project.objects.count() == 1
    assert Environment.objects.count() == 2
    assert Feature.objects.count() == 3
    assert FeatureStateValue.objects.count() == 6
    assert MultivariateFeatureOption.objects.count() == 6
    assert MultivariateFeatureStateValue.objects.count() == 12


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
