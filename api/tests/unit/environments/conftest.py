import typing
from unittest.mock import Mock

import pytest
from pytest_mock import MockerFixture


@pytest.fixture()
def mock_dynamo_env_wrapper(mocker: MockerFixture) -> Mock:
    return mocker.patch("environments.models.environment_wrapper")


@pytest.fixture()
def mock_dynamo_env_v2_wrapper(mocker: MockerFixture) -> Mock:
    return mocker.patch("environments.models.environment_v2_wrapper")


@pytest.fixture()
def enable_v2_versioning_for_new_environments(
    mocker: MockerFixture,
) -> typing.Callable[[], None]:
    """
    This fixture returns a callable that allows us to enable the flag such that new environments
    are created with feature versioning v2 enabled. It returns a callable to ensure that we can
    control when the flag is enabled in the test code, to ensure that other fixtures are unaffected.

    Relevant issue for improving this: https://github.com/Flagsmith/flagsmith-python-client/issues/135
    """

    def _enable_v2_versioning_for_new_environments() -> None:
        mock_flagsmith_client = mocker.MagicMock()
        mocker.patch(
            "environments.models.get_client", return_value=mock_flagsmith_client
        )

        mocked_identity_flags = mock_flagsmith_client.get_identity_flags.return_value

        def is_feature_enabled(feature_name: str) -> bool:
            return feature_name == "enable_feature_versioning_for_new_environments"

        mocked_identity_flags.is_feature_enabled.side_effect = is_feature_enabled

    return _enable_v2_versioning_for_new_environments
