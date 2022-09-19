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
    mocker, rf, forwarder_mocked_migrator, forwarder_function
):
    # Given
    project_id = 1

    mocked_requests = mocker.patch(
        "edge_api.identities.edge_request_forwarder.requests"
    )

    mocked_migration_done = mocker.PropertyMock(return_value=False)
    type(
        forwarder_mocked_migrator.return_value
    ).is_migration_done = mocked_migration_done

    # When
    forwarder_function("GET", {}, project_id, None)

    # Then
    assert mocked_requests.mock_calls == []

    forwarder_mocked_migrator.assert_called_with(project_id)


def test_forward_identity_request_sync_makes_correct_get_request(
    mocker,
    forward_enable_settings,
    forwarder_mocked_migrator,
):
    # Given
    project_id = 1

    query_params = {"identifier": "test_123"}
    api_key = "test_api_key"
    headers = {"X-Environment-Key": api_key}

    mocked_requests = mocker.patch(
        "edge_api.identities.edge_request_forwarder.requests"
    )

    mocked_migration_done = mocker.PropertyMock(return_value=True)
    type(
        forwarder_mocked_migrator.return_value
    ).is_migration_done = mocked_migration_done

    # When
    forward_identity_request_sync("GET", headers, project_id, query_params)

    # Then
    args, kwargs = mocked_requests.get.call_args
    assert args[0] == forward_enable_settings.EDGE_API_URL + "identities/"
    assert kwargs["params"] == query_params
    assert kwargs["headers"]["X-Environment-Key"] == api_key
    assert kwargs["headers"][FLAGSMITH_SIGNATURE_HEADER]

    forwarder_mocked_migrator.assert_called_with(project_id)


def test_forward_identity_request_sync_makes_correct_post_request(
    mocker, forward_enable_settings, forwarder_mocked_migrator
):
    # Given
    project_id = 1

    request_data = {"key": "value"}
    api_key = "test_api_key"
    headers = {"X-Environment-Key": api_key}

    mocked_requests = mocker.patch(
        "edge_api.identities.edge_request_forwarder.requests"
    )

    mocked_migration_done = mocker.MagicMock(return_value=True)
    type(
        forwarder_mocked_migrator.return_value
    ).is_migration_done = mocked_migration_done

    # When
    forward_identity_request_sync(
        "POST", headers, project_id, request_data=request_data
    )

    # Then
    args, kwargs = mocked_requests.post.call_args
    assert args[0] == forward_enable_settings.EDGE_API_URL + "identities/"

    assert kwargs["data"] == json.dumps(request_data)
    assert kwargs["headers"]["X-Environment-Key"] == api_key
    assert kwargs["headers"][FLAGSMITH_SIGNATURE_HEADER]

    forwarder_mocked_migrator.assert_called_with(project_id)


def test_forward_trait_request_sync_makes_correct_post_request(
    mocker, forward_enable_settings, forwarder_mocked_migrator
):
    # Given
    project_id = 1
    request_data = {
        "identity": {"identifier": "test_user_123"},
        "trait_key": "key",
        "trait_value": "value",
    }
    api_key = "test_api_key"
    headers = {"X-Environment-Key": api_key}

    mocked_requests = mocker.patch(
        "edge_api.identities.edge_request_forwarder.requests"
    )

    mocked_migration_done = mocker.MagicMock(return_value=True)
    type(
        forwarder_mocked_migrator.return_value
    ).is_migration_done = mocked_migration_done

    # When
    forward_trait_request_sync("POST", headers, project_id, payload=request_data)

    # Then
    args, kwargs = mocked_requests.post.call_args
    assert args[0] == forward_enable_settings.EDGE_API_URL + "traits/"

    assert kwargs["data"] == json.dumps(request_data)
    assert kwargs["headers"]["X-Environment-Key"] == api_key
    assert kwargs["headers"][FLAGSMITH_SIGNATURE_HEADER]

    forwarder_mocked_migrator.assert_called_with(project_id)
