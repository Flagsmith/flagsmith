from unittest.mock import MagicMock

import pytest
from flagsmith.offline_handlers import LocalFileHandler
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from integrations.flagsmith.client import get_client
from integrations.flagsmith.exceptions import FlagsmithIntegrationError
from integrations.flagsmith.flagsmith_service import ENVIRONMENT_JSON_PATH


@pytest.fixture(autouse=True)
def reset_globals(mocker: MockerFixture) -> None:  # type: ignore[misc]
    mocker.patch("integrations.flagsmith.client._flagsmith_clients", {})
    yield


@pytest.fixture()
def mock_local_file_handler(mocker: MockerFixture) -> None:
    return mocker.MagicMock(spec=LocalFileHandler)  # type: ignore[no-any-return]


@pytest.fixture()
def mock_local_file_handler_class(  # type: ignore[no-untyped-def]
    mocker: MockerFixture, mock_local_file_handler: MagicMock
):
    return mocker.patch(
        "integrations.flagsmith.client.LocalFileHandler",
        return_value=mock_local_file_handler,
    )


def test_get_client_initialises_flagsmith_with_correct_arguments_offline_mode_disabled(  # type: ignore[no-untyped-def]  # noqa: E501
    settings: SettingsWrapper,
    mocker: MockerFixture,
    mock_local_file_handler,
    mock_local_file_handler_class,
) -> None:
    # Given
    server_key = "some-key"
    api_url = "https://my.flagsmith.api/api/v1/"

    settings.FLAGSMITH_ON_FLAGSMITH_SERVER_KEY = server_key
    settings.FLAGSMITH_ON_FLAGSMITH_SERVER_API_URL = api_url
    settings.FLAGSMITH_ON_FLAGSMITH_SERVER_OFFLINE_MODE = False

    mock_flagsmith_class = mocker.patch("integrations.flagsmith.client.Flagsmith")

    # When
    client = get_client()

    # Then
    assert client == mock_flagsmith_class.return_value

    mock_flagsmith_class.assert_called_once()

    call_args = mock_flagsmith_class.call_args
    assert call_args.kwargs["environment_key"] == server_key
    assert call_args.kwargs["api_url"] == api_url
    assert "offline_mode" not in call_args.kwargs
    assert call_args.kwargs["offline_handler"] == mock_local_file_handler

    mock_local_file_handler_class.assert_called_once_with(ENVIRONMENT_JSON_PATH)


def test_get_client_initialises_flagsmith_with_correct_arguments_offline_mode_enabled(  # type: ignore[no-untyped-def]
    settings: SettingsWrapper,
    mocker: MockerFixture,
    mock_local_file_handler,
    mock_local_file_handler_class,
) -> None:
    # Given
    settings.FLAGSMITH_ON_FLAGSMITH_SERVER_OFFLINE_MODE = True

    mock_flagsmith_class = mocker.patch("integrations.flagsmith.client.Flagsmith")

    # When
    client = get_client()

    # Then
    assert client == mock_flagsmith_class.return_value

    mock_flagsmith_class.assert_called_once()

    call_args = mock_flagsmith_class.call_args
    assert call_args.kwargs["offline_mode"] is True
    assert call_args.kwargs["offline_handler"] == mock_local_file_handler

    mock_local_file_handler_class.assert_called_once_with(ENVIRONMENT_JSON_PATH)


def test_get_client_raises_value_error_if_missing_args(  # type: ignore[no-untyped-def]
    settings: SettingsWrapper, mock_local_file_handler_class
):
    # Given
    settings.FLAGSMITH_ON_FLAGSMITH_SERVER_OFFLINE_MODE = False
    assert settings.FLAGSMITH_ON_FLAGSMITH_SERVER_KEY is None

    # When
    with pytest.raises(FlagsmithIntegrationError):
        get_client()
