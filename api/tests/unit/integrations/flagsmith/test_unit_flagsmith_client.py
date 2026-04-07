from unittest.mock import MagicMock

import pytest
from flagsmith.offline_handlers import LocalFileHandler
from openfeature.provider import ProviderStatus
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from integrations.flagsmith.client import (
    DEFAULT_OPENFEATURE_DOMAIN,
    get_openfeature_client,
    get_provider_kwargs,
    initialise_provider,
)
from integrations.flagsmith.exceptions import FlagsmithIntegrationError
from integrations.flagsmith.flagsmith_service import ENVIRONMENT_JSON_PATH


@pytest.fixture()
def mock_local_file_handler(mocker: MockerFixture) -> MagicMock:
    mock: MagicMock = mocker.MagicMock(spec=LocalFileHandler)
    return mock


@pytest.fixture()
def mock_local_file_handler_class(
    mocker: MockerFixture, mock_local_file_handler: MagicMock
) -> MagicMock:
    return mocker.patch(
        "integrations.flagsmith.client.LocalFileHandler",
        return_value=mock_local_file_handler,
    )


def test_get_openfeature_client__provider_not_ready__initialises_provider(
    settings: SettingsWrapper,
    mocker: MockerFixture,
    mock_local_file_handler: MagicMock,
    mock_local_file_handler_class: MagicMock,
) -> None:
    # Given
    settings.FLAGSMITH_ON_FLAGSMITH_SERVER_OFFLINE_MODE = True

    mock_openfeature_api = mocker.patch("integrations.flagsmith.client.openfeature_api")
    mock_client = mock_openfeature_api.get_client.return_value
    mock_client.get_provider_status.return_value = ProviderStatus.NOT_READY

    mock_flagsmith_class = mocker.patch("integrations.flagsmith.client.Flagsmith")
    mock_provider_class = mocker.patch(
        "integrations.flagsmith.client.FlagsmithProvider"
    )

    # When
    client = get_openfeature_client()

    # Then
    assert client == mock_client
    mock_flagsmith_class.assert_called_once()
    mock_provider_class.assert_called_once_with(
        client=mock_flagsmith_class.return_value,
    )
    mock_openfeature_api.set_provider.assert_called_once_with(
        mock_provider_class.return_value,
        domain=DEFAULT_OPENFEATURE_DOMAIN,
    )


def test_get_openfeature_client__provider_ready__skips_initialisation(
    mocker: MockerFixture,
) -> None:
    # Given
    mock_openfeature_api = mocker.patch("integrations.flagsmith.client.openfeature_api")
    mock_client = mock_openfeature_api.get_client.return_value
    mock_client.get_provider_status.return_value = ProviderStatus.READY

    mock_flagsmith_class = mocker.patch("integrations.flagsmith.client.Flagsmith")

    # When
    client = get_openfeature_client()

    # Then
    assert client == mock_client
    mock_flagsmith_class.assert_not_called()
    mock_openfeature_api.set_provider.assert_not_called()


def test_initialise_provider__offline_mode_disabled__initialises_with_server_key(
    settings: SettingsWrapper,
    mocker: MockerFixture,
    mock_local_file_handler: MagicMock,
    mock_local_file_handler_class: MagicMock,
) -> None:
    # Given
    server_key = "some-key"
    api_url = "https://my.flagsmith.api/api/v1/"

    settings.FLAGSMITH_ON_FLAGSMITH_SERVER_KEY = server_key
    settings.FLAGSMITH_ON_FLAGSMITH_SERVER_API_URL = api_url
    settings.FLAGSMITH_ON_FLAGSMITH_SERVER_OFFLINE_MODE = False

    mock_flagsmith_class = mocker.patch("integrations.flagsmith.client.Flagsmith")
    mock_provider_class = mocker.patch(
        "integrations.flagsmith.client.FlagsmithProvider"
    )
    mock_openfeature_api = mocker.patch("integrations.flagsmith.client.openfeature_api")

    # When
    initialise_provider(**get_provider_kwargs())

    # Then
    mock_flagsmith_class.assert_called_once()
    call_args = mock_flagsmith_class.call_args
    assert call_args.kwargs["environment_key"] == server_key
    assert call_args.kwargs["api_url"] == api_url
    assert call_args.kwargs["enable_local_evaluation"] is True
    assert "offline_mode" not in call_args.kwargs
    assert call_args.kwargs["offline_handler"] == mock_local_file_handler

    mock_provider_class.assert_called_once_with(
        client=mock_flagsmith_class.return_value,
    )
    mock_openfeature_api.set_provider.assert_called_once_with(
        mock_provider_class.return_value,
        domain=DEFAULT_OPENFEATURE_DOMAIN,
    )

    mock_local_file_handler_class.assert_called_once_with(ENVIRONMENT_JSON_PATH)


def test_initialise_provider__offline_mode_enabled__initialises_with_offline_handler(
    settings: SettingsWrapper,
    mocker: MockerFixture,
    mock_local_file_handler: MagicMock,
    mock_local_file_handler_class: MagicMock,
) -> None:
    # Given
    settings.FLAGSMITH_ON_FLAGSMITH_SERVER_OFFLINE_MODE = True

    mock_flagsmith_class = mocker.patch("integrations.flagsmith.client.Flagsmith")
    mock_provider_class = mocker.patch(
        "integrations.flagsmith.client.FlagsmithProvider"
    )
    mock_openfeature_api = mocker.patch("integrations.flagsmith.client.openfeature_api")

    # When
    initialise_provider(**get_provider_kwargs())

    # Then
    mock_flagsmith_class.assert_called_once()
    call_args = mock_flagsmith_class.call_args
    assert call_args.kwargs["offline_mode"] is True
    assert call_args.kwargs["enable_local_evaluation"] is True
    assert call_args.kwargs["offline_handler"] == mock_local_file_handler

    mock_provider_class.assert_called_once_with(
        client=mock_flagsmith_class.return_value,
    )
    mock_openfeature_api.set_provider.assert_called_once_with(
        mock_provider_class.return_value,
        domain=DEFAULT_OPENFEATURE_DOMAIN,
    )

    mock_local_file_handler_class.assert_called_once_with(ENVIRONMENT_JSON_PATH)


def test_get_provider_kwargs__missing_server_key__raises_error(
    settings: SettingsWrapper, mock_local_file_handler_class: MagicMock
) -> None:
    # Given
    settings.FLAGSMITH_ON_FLAGSMITH_SERVER_OFFLINE_MODE = False
    assert settings.FLAGSMITH_ON_FLAGSMITH_SERVER_KEY is None

    # When / Then
    with pytest.raises(FlagsmithIntegrationError):
        get_provider_kwargs()
