import pytest


@pytest.fixture()
def mock_dynamo_env_wrapper(mocker):
    return mocker.patch("environments.models.environment_wrapper")
