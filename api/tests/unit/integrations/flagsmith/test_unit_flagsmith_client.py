import pytest
from flagsmith.offline_handlers import LocalFileHandler

from integrations.flagsmith.client import get_client
from integrations.flagsmith.flagsmith_service import ENVIRONMENT_JSON_PATH


@pytest.fixture(autouse=True)
def reset_globals(mocker):
    mocker.patch("integrations.flagsmith.client._flagsmith_client", None)
    yield


def test_get_client_initialises_flagsmith_with_correct_arguments_offline_mode_disabled(
    settings, mocker
) -> None:
    # Given
    server_key = "some-key"
    api_url = "https://my.flagsmith.api/api/v1/"

    settings.FLAGSMITH_SERVER_KEY = server_key
    settings.FLAGSMITH_API_URL = api_url
    settings.FLAGSMITH_OFFLINE_MODE = False

    mock_local_file_handler = mocker.MagicMock(spec=LocalFileHandler)

    mock_flagsmith_class = mocker.patch("integrations.flagsmith.client.Flagsmith")
    mock_local_file_handler_class = mocker.patch(
        "integrations.flagsmith.client.LocalFileHandler",
        return_value=mock_local_file_handler,
    )

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


def test_get_client_initialises_flagsmith_with_correct_arguments_offline_mode_enabled(
    settings, mocker
) -> None:
    # Given
    settings.FLAGSMITH_OFFLINE_MODE = True

    mock_local_file_handler = mocker.MagicMock(spec=LocalFileHandler)

    mock_flagsmith_class = mocker.patch("integrations.flagsmith.client.Flagsmith")
    mock_local_file_handler_class = mocker.patch(
        "integrations.flagsmith.client.LocalFileHandler",
        return_value=mock_local_file_handler,
    )

    # When
    client = get_client()

    # Then
    assert client == mock_flagsmith_class.return_value

    mock_flagsmith_class.assert_called_once()

    call_args = mock_flagsmith_class.call_args
    assert call_args.kwargs["offline_mode"] is True
    assert call_args.kwargs["offline_handler"] == mock_local_file_handler

    mock_local_file_handler_class.assert_called_once_with(ENVIRONMENT_JSON_PATH)
