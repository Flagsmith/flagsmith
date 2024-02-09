import json
from os.path import abspath, dirname, join
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from integrations.launch_darkly.client import LaunchDarklyClient
from integrations.launch_darkly.models import LaunchDarklyImportRequest
from integrations.launch_darkly.services import create_import_request
from projects.models import Project
from users.models import FFAdminUser


@pytest.fixture
def ld_project_key() -> str:
    return "test-project-key"


@pytest.fixture
def ld_token() -> str:
    return "test-token"


@pytest.fixture
def ld_client_mock(mocker: MockerFixture) -> MagicMock:
    ld_client_mock = mocker.MagicMock(spec=LaunchDarklyClient)

    for method_name, response_data_path in {
        "get_project": "client_responses/get_project.json",
        "get_environments": "client_responses/get_environments.json",
        "get_flags": "client_responses/get_flags.json",
        "get_segments": "client_responses/get_segments.json",
    }.items():
        getattr(ld_client_mock, method_name).return_value = json.load(
            open(join(dirname(abspath(__file__)), response_data_path))
        )

    ld_client_mock.get_flag_count.return_value = 9
    ld_client_mock.get_flag_tags.return_value = ["testtag", "testtag2"]

    return ld_client_mock


@pytest.fixture
def ld_client_class_mock(
    mocker: MockerFixture,
    ld_client_mock: MagicMock,
) -> MagicMock:
    return mocker.patch(
        "integrations.launch_darkly.services.LaunchDarklyClient",
        return_value=ld_client_mock,
    )


@pytest.fixture
def import_request(
    ld_client_class_mock: MagicMock,
    project: Project,
    test_user: FFAdminUser,
    ld_project_key: str,
    ld_token: str,
) -> LaunchDarklyImportRequest:
    return create_import_request(
        project=project,
        user=test_user,
        ld_project_key=ld_project_key,
        ld_token=ld_token,
    )
