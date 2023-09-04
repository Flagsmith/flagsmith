import json
from unittest.mock import mock_open, patch

import pytest
import responses

from integrations.flagsmith.exceptions import FlagsmithIntegrationError
from integrations.flagsmith.flagsmith_service import update_environment_json


@pytest.fixture()
def environment_document():
    """
    An example environment document as returned from the API.
    """
    return {
        "id": 1,
        "api_key": "some-key",
        "project": {
            "id": 1,
            "name": "Test Project",
            "organisation": {
                "id": 1,
                "name": "Test Organisation",
                "feature_analytics": False,
                "stop_serving_flags": False,
                "persist_trait_data": True,
            },
            "hide_disabled_flags": False,
            "segments": [],
            "enable_realtime_updates": False,
            "server_key_only_feature_ids": [],
        },
        "feature_states": [
            {
                "feature": {"id": 1, "name": "test", "type": "STANDARD"},
                "enabled": False,
                "django_id": 1,
                "feature_segment": None,
                "featurestate_uuid": "ec33a926-0b7e-4eb7-b02b-bf9df2ffa53e",
                "feature_state_value": None,
                "multivariate_feature_state_values": [],
            }
        ],
        "name": "Test",
        "allow_client_traits": True,
        "updated_at": "2023-08-01T14:00:36.347565+00:00",
        "hide_sensitive_data": False,
        "hide_disabled_flags": None,
        "use_identity_composite_key_for_hashing": True,
        "amplitude_config": None,
        "dynatrace_config": None,
        "heap_config": None,
        "mixpanel_config": None,
        "rudderstack_config": None,
        "segment_config": None,
        "webhook_config": None,
    }


@responses.activate
def test_update_environment_json(settings, environment_document):
    """
    Test to verify that, when we call update_environment_json, the response is written
    to the correct file and that the sensitive data from the response is masked.
    """
    # Given
    api_url = "https://api.flagsmith.com/api/v1"
    settings.FLAGSMITH_ON_FLAGSMITH_SERVER_API_URL = api_url

    responses.add(
        method="GET",
        url=f"{api_url}/environment-document",
        body=json.dumps(environment_document),
        status=200,
    )

    # When
    with patch("builtins.open", mock_open(read_data="")) as mocked_open:
        update_environment_json()

    # Then
    written_json = json.loads(mocked_open.return_value.write.call_args[0][0])
    assert written_json["id"] == 0
    assert written_json["api_key"] == "masked"
    assert written_json["feature_states"] == environment_document["feature_states"]
    assert written_json["project"]["id"] == 0
    assert written_json["project"]["segments"] == []
    assert written_json["project"]["organisation"]["id"] == 0


@responses.activate
def test_update_environment_json_throws_exception_for_failed_request(settings):
    # Given
    api_url = "https://api.flagsmith.com/api/v1"
    settings.FLAGSMITH_ON_FLAGSMITH_SERVER_API_URL = api_url

    responses.add(
        method="GET",
        url=f"{api_url}/environment-document",
        status=404,
    )

    # When
    with pytest.raises(FlagsmithIntegrationError):
        update_environment_json()
