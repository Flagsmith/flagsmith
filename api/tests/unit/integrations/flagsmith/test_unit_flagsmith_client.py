from unittest.mock import MagicMock

import openfeature.api as openfeature_api
import pytest
from flagsmith.offline_handlers import LocalFileHandler
from openfeature.provider.in_memory_provider import InMemoryProvider
from openfeature.provider.metadata import Metadata
from openfeature.provider.no_op_metadata import NoOpMetadata
from openfeature_flagsmith.provider import FlagsmithProvider
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


def test_get_openfeature_client__default_provider__initialises_provider(
    settings: SettingsWrapper,
    mocker: MockerFixture,
    mock_local_file_handler: MagicMock,
    mock_local_file_handler_class: MagicMock,
) -> None:
    # Given
    settings.FLAGSMITH_ON_FLAGSMITH_SERVER_OFFLINE_MODE = True

    mock_openfeature_api = mocker.patch("integrations.flagsmith.client.openfeature_api")
    mock_openfeature_api.get_provider_metadata.return_value = NoOpMetadata()
    mock_client = mock_openfeature_api.get_client.return_value

    mock_flagsmith_class = mocker.patch("integrations.flagsmith.client.Flagsmith")

    # When
    client = get_openfeature_client()

    # Then
    assert client == mock_client
    mock_flagsmith_class.assert_called_once()
    mock_openfeature_api.set_provider.assert_called_once()
    (provider_arg,) = mock_openfeature_api.set_provider.call_args.args
    assert isinstance(provider_arg, FlagsmithProvider)
    assert mock_openfeature_api.set_provider.call_args.kwargs == {
        "domain": DEFAULT_OPENFEATURE_DOMAIN,
    }


def test_get_openfeature_client__non_default_provider__skips_initialisation(
    mocker: MockerFixture,
) -> None:
    # Given
    # Any provider explicitly bound to the domain — including test doubles
    # like `InMemoryProvider` from the `enable_features` fixture — must be
    # preserved by `get_openfeature_client`.
    mock_openfeature_api = mocker.patch("integrations.flagsmith.client.openfeature_api")
    mock_openfeature_api.get_provider_metadata.return_value = Metadata(
        name="some-other-provider",
    )
    mock_client = mock_openfeature_api.get_client.return_value

    mock_flagsmith_class = mocker.patch("integrations.flagsmith.client.Flagsmith")

    # When
    client = get_openfeature_client()

    # Then
    assert client == mock_client
    mock_flagsmith_class.assert_not_called()
    mock_openfeature_api.set_provider.assert_not_called()


def test_get_openfeature_client__first_call__installs_flagsmith_provider_for_domain(
    settings: SettingsWrapper,
    mocker: MockerFixture,
    mock_local_file_handler_class: MagicMock,
) -> None:
    # Given
    # `openfeature_api` is intentionally NOT mocked so the real provider
    # registry is exercised: an uninitialised domain falls back to a ready
    # `NoOpProvider`, so a naive `status != READY` guard never triggers
    # initialisation and every evaluation silently returns the default.
    settings.FLAGSMITH_ON_FLAGSMITH_SERVER_OFFLINE_MODE = True
    mocker.patch("integrations.flagsmith.client.Flagsmith")
    openfeature_api.clear_providers()

    # When
    get_openfeature_client()

    # Then
    installed_provider = openfeature_api.get_client(
        domain=DEFAULT_OPENFEATURE_DOMAIN
    ).provider
    assert isinstance(installed_provider, FlagsmithProvider)

    # Cleanup
    openfeature_api.clear_providers()


def test_get_openfeature_client__externally_installed_provider__preserved(
    mocker: MockerFixture,
) -> None:
    # Given
    # Exercised against the real `openfeature_api` to confirm the
    # `enable_features` fixture's `InMemoryProvider` survives a call to
    # `get_openfeature_client`.
    mocker.patch("integrations.flagsmith.client.Flagsmith")
    openfeature_api.clear_providers()
    in_memory_provider = InMemoryProvider({})
    openfeature_api.set_provider(in_memory_provider, domain=DEFAULT_OPENFEATURE_DOMAIN)

    # When
    get_openfeature_client()

    # Then
    installed_provider = openfeature_api.get_client(
        domain=DEFAULT_OPENFEATURE_DOMAIN
    ).provider
    assert installed_provider is in_memory_provider

    # Cleanup
    openfeature_api.clear_providers()


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
