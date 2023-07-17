import json
import os.path
from unittest.mock import mock_open, patch

import pytest

from integrations.flagsmith.client import get_client


@pytest.fixture(autouse=True)
def reset_globals(mocker):
    mocker.patch("integrations.flagsmith.client._defaults", None)
    mocker.patch("integrations.flagsmith.client._flagsmith_client", None)
    yield


def test_get_client_handles_missing_flagsmith_settings(settings) -> None:
    # Given
    assert settings.FLAGSMITH_SERVER_KEY is None
    assert settings.FLAGSMITH_API_URL is None

    # When
    client = get_client()

    # Then
    assert client.get_environment_flags().flags == {}
    assert client.get_identity_flags("identifier").flags == {}


def test_get_client_sets_up_default_flags(settings) -> None:
    # Given
    assert settings.FLAGSMITH_SERVER_KEY is None
    assert settings.FLAGSMITH_API_URL is None

    feature_name = "my_feature"
    feature_value = 42
    feature_enabled = True

    defaults_data = json.dumps(
        [
            {
                "feature_state_value": feature_value,
                "enabled": feature_enabled,
                "feature": {"id": 1, "type": "STANDARD", "name": feature_name},
            }
        ]
    )

    # When
    with patch("builtins.open", mock_open(read_data=defaults_data)) as mock_file:
        client = get_client()

        # Then
        mock_file.assert_called_with(
            os.path.join(settings.BASE_DIR, "integrations/flagsmith/defaults.json")
        )

        # let's verify that it's using the defaults as we expect
        flags = client.get_environment_flags()
        assert flags.is_feature_enabled(feature_name) == feature_enabled
        assert flags.get_feature_value(feature_name) == feature_value


def test_get_client_initialises_flagsmith_with_correct_arguments(
    settings, mocker
) -> None:
    # Given
    server_key = "some-key"
    api_url = "https://my.flagsmith.api/api/v1/"

    settings.FLAGSMITH_SERVER_KEY = server_key
    settings.FLAGSMITH_API_URL = api_url

    mock_flagsmith_class = mocker.patch(
        "integrations.flagsmith.client._WrappedFlagsmith"
    )

    # When
    client = get_client()

    # Then
    assert client == mock_flagsmith_class.return_value

    mock_flagsmith_class.assert_called_once()

    call_args = mock_flagsmith_class.call_args
    assert call_args.kwargs["environment_key"] == server_key
    assert call_args.kwargs["api_url"] == api_url
    assert call_args.kwargs["default_flag_handler"]
