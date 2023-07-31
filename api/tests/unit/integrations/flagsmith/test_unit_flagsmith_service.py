import json
from unittest.mock import mock_open, patch

import pytest
import responses

from integrations.flagsmith.exceptions import FlagsmithIntegrationError
from integrations.flagsmith.flagsmith_service import update_environment_json


@responses.activate
def test_update_environment_json(settings):
    # Given
    api_url = "https://api.flagsmith.com/api/v1"
    settings.FLAGSMITH_API_URL = api_url

    environment_document = {"api_key": "some-key", "name": "test"}
    environment_json = json.dumps(environment_document)

    responses.add(
        method="GET",
        url=f"{api_url}/environment-document",
        body=environment_json,
        status=200,
    )

    # When
    with patch("builtins.open", mock_open(read_data="")) as mocked_open:
        update_environment_json()

    # Then
    mocked_open.return_value.write.assert_called_once_with(environment_json)


@responses.activate
def test_update_environment_json_throws_exception_for_failed_request(settings):
    # Given
    api_url = "https://api.flagsmith.com/api/v1"
    settings.FLAGSMITH_API_URL = api_url

    responses.add(
        method="GET",
        url=f"{api_url}/environment-document",
        status=404,
    )

    # When
    with pytest.raises(FlagsmithIntegrationError):
        update_environment_json()
