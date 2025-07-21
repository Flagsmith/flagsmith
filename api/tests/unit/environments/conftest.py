from unittest.mock import Mock

import pytest
from pytest_mock import MockerFixture


@pytest.fixture()
def mock_dynamo_env_wrapper(mocker: MockerFixture) -> Mock:
    return mocker.patch("environments.models.environment_wrapper")


@pytest.fixture()
def mock_dynamo_env_v2_wrapper(mocker: MockerFixture) -> Mock:
    return mocker.patch("environments.models.environment_v2_wrapper")
