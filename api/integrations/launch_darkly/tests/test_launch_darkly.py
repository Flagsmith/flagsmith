from unittest.mock import MagicMock

import pytest

from integrations.launch_darkly.client import LaunchDarklyClient
from integrations.launch_darkly.launch_darkly import LaunchDarklyWrapper


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
def test_launch_darkly_import(ld_project_response, ld_env_response, ld_flags_response):
    # Given
    ld_client_mock = _build_launch_darkly_client_mock(
        ld_project_response, ld_env_response, ld_flags_response
    )

    # When
    LaunchDarklyWrapper(
        client=ld_client_mock, request=None, api_key=None, user=None
    ).import_data()

    # Then
    assert False


def _build_launch_darkly_client_mock(
    ld_project_response, ld_env_response, ld_flags_response
):
    project_response = {}
    env_response = []
    flags_response = []
    ld_client_mock = MagicMock(spec=LaunchDarklyClient)
    ld_client_mock.get_project.return_value = project_response
    ld_client_mock.get_environments.return_value = env_response
    ld_client_mock.get_flags.return_value = flags_response
    return ld_client_mock
