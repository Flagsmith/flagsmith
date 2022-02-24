import json

import pytest
from core.constants import FLAGSMITH_SIGNATURE_HEADER

from edge_api.identities.edge_request_forwarder import (
    forward_identity_request_sync,
    forward_trait_request_sync,
)


@pytest.mark.parametrize(
    "forwarder_function", [forward_identity_request_sync, forward_trait_request_sync]
)
def test_forwarder_sync_function_makes_no_request_if_migration_is_not_yet_done(
    mocker, rf, forwarder_dynamo_wrapper, forwarder_function
):
    # Given
    request = rf.get("/url")
    project_id = 1

    mocked_requests = mocker.patch(
        "edge_api.identities.edge_request_forwarder.requests"
    )

    mocked_migration_done = mocker.MagicMock(return_value=False)
    forwarder_dynamo_wrapper.return_value.is_migration_done = mocked_migration_done

    # When
    forwarder_function(request, project_id)

    # Then
    assert mocked_requests.mock_calls == []

    forwarder_dynamo_wrapper.assert_called_with()
    mocked_migration_done.assert_called_with(project_id)


def test_forward_identity_request_sync_makes_correct_get_request(
    mocker,
    rf,
    forward_enable_settings,
    forwarder_dynamo_wrapper,
):
    # Given
    project_id = 1

    query_params = {"identifier": "test_123"}
    api_key = "test_api_key"
    request = rf.get("/identities", query_params, HTTP_X_Environment_key=api_key)

    mocked_requests = mocker.patch(
        "edge_api.identities.edge_request_forwarder.requests"
    )

    mocked_migration_done = mocker.MagicMock(return_value=True)
    forwarder_dynamo_wrapper.return_value.is_migration_done = mocked_migration_done

    # When
    forward_identity_request_sync(request, project_id)

    # Then
    args, kwargs = mocked_requests.get.call_args
    assert args[0] == forward_enable_settings.EDGE_API_URL + "identities/"
    assert kwargs["params"] == query_params
    assert kwargs["headers"]["X-Environment-Key"] == api_key
    assert kwargs["headers"][FLAGSMITH_SIGNATURE_HEADER]

    forwarder_dynamo_wrapper.assert_called_with()
    mocked_migration_done.assert_called_with(project_id)


def test_forward_identity_request_sync_makes_correct_post_request(
    mocker, rf, forward_enable_settings, forwarder_dynamo_wrapper
):
    # Given
    project_id = 1

    request_data = {"key": "value"}
    api_key = "test_api_key"
    request = rf.post("/identities", HTTP_X_Environment_key=api_key)
    request.data = request_data

    mocked_requests = mocker.patch(
        "edge_api.identities.edge_request_forwarder.requests"
    )

    mocked_migration_done = mocker.MagicMock(return_value=True)
    forwarder_dynamo_wrapper.return_value.is_migration_done = mocked_migration_done

    # When
    forward_identity_request_sync(request, project_id)

    # Then
    args, kwargs = mocked_requests.post.call_args
    assert args[0] == forward_enable_settings.EDGE_API_URL + "identities/"

    assert kwargs["data"] == json.dumps(request_data)
    assert kwargs["headers"]["X-Environment-Key"] == api_key
    assert kwargs["headers"][FLAGSMITH_SIGNATURE_HEADER]

    forwarder_dynamo_wrapper.assert_called_with()
    mocked_migration_done.assert_called_with(project_id)


def test_forward_trait_request_sync_makes_correct_post_request_when_payload_is_none(
    mocker, rf, forward_enable_settings, forwarder_dynamo_wrapper
):
    # Given
    project_id = 1
    request_data = {
        "identity": {"identifier": "test_user_123"},
        "trait_key": "key",
        "trait_value": "value",
    }
    api_key = "test_api_key"
    request = rf.post("/traits", HTTP_X_Environment_key=api_key)
    request.data = request_data
    mocked_requests = mocker.patch(
        "edge_api.identities.edge_request_forwarder.requests"
    )

    mocked_migration_done = mocker.MagicMock(return_value=True)
    forwarder_dynamo_wrapper.return_value.is_migration_done = mocked_migration_done

    # When
    forward_trait_request_sync(request, project_id, payload=None)

    # Then
    args, kwargs = mocked_requests.post.call_args
    assert args[0] == forward_enable_settings.EDGE_API_URL + "traits/"

    assert kwargs["data"] == json.dumps(request_data)
    assert kwargs["headers"]["X-Environment-Key"] == api_key
    assert kwargs["headers"][FLAGSMITH_SIGNATURE_HEADER]

    forwarder_dynamo_wrapper.assert_called_with()
    mocked_migration_done.assert_called_with(project_id)


def test_forward_trait_request_sync_uses_payload_over_request_data_if_not_none(
    mocker, rf, forward_enable_settings, forwarder_dynamo_wrapper
):
    # Given
    project_id = 1
    payload = {
        "identity": {"identifier": "test_user_123"},
        "trait_key": "key",
        "trait_value": "value",
    }
    request_data = {"key": "value"}

    api_key = "test_api_key"
    request = rf.post("/traits", HTTP_X_Environment_key=api_key)
    request.data = request_data

    mocked_migration_done = mocker.MagicMock(return_value=True)
    forwarder_dynamo_wrapper.return_value.is_migration_done = mocked_migration_done

    mocked_requests = mocker.patch(
        "edge_api.identities.edge_request_forwarder.requests"
    )
    # When
    forward_trait_request_sync(request, project_id, payload)

    # Then
    args, kwargs = mocked_requests.post.call_args
    assert args[0] == forward_enable_settings.EDGE_API_URL + "traits/"

    assert kwargs["data"] == json.dumps(payload)
    assert kwargs["headers"]["X-Environment-Key"] == api_key
    assert kwargs["headers"][FLAGSMITH_SIGNATURE_HEADER]

    forwarder_dynamo_wrapper.assert_called_with()
    mocked_migration_done.assert_called_with(project_id)
