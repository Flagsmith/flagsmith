from datetime import datetime

import pytest

from sse.exceptions import SSEAuthTokenNotSet
from sse.tasks import (
    get_auth_header,
    send_environment_update_message,
    send_environment_update_message_for_project,
    send_identity_update_message,
    send_identity_update_messages,
)


def test_send_environment_update_message_for_project_make_correct_request(
    mocker,
    settings,
    realtime_enabled_project,
    realtime_enabled_project_environment_one,
    realtime_enabled_project_environment_two,
):
    # Given
    base_url = "http://localhost:8000"
    token = "token"

    settings.SSE_SERVER_BASE_URL = base_url
    settings.SSE_AUTHENTICATION_TOKEN = token
    mocked_requests = mocker.patch("sse.tasks.requests")

    # When
    send_environment_update_message_for_project(realtime_enabled_project.id)

    # Then
    mocked_requests.post.has_calls(
        mocker.call(
            f"{base_url}/sse/environments/{realtime_enabled_project_environment_one.api_key}/queue-change",
            headers={"Authorization": f"Token {token}"},
            json={
                "updated_at": realtime_enabled_project_environment_one.updated_at.isoformat()
            },
        ),
        mocker.call(
            f"{base_url}/sse/environments/{realtime_enabled_project_environment_two.api_key}/queue-change",
            headers={"Authorization": f"Token {token}"},
            json={
                "updated_at": realtime_enabled_project_environment_two.updated_at.isoformat()
            },
        ),
    )


def test_send_environment_update_message_make_correct_request(mocker, settings):
    # Given
    base_url = "http://localhost:8000"
    token = "token"
    environment_key = "test_environment"
    updated_at = datetime.now().isoformat()

    settings.SSE_SERVER_BASE_URL = base_url
    settings.SSE_AUTHENTICATION_TOKEN = token
    mocked_requests = mocker.patch("sse.tasks.requests")

    # When
    send_environment_update_message(environment_key, updated_at)

    # Then
    mocked_requests.post.assert_called_once_with(
        f"{base_url}/sse/environments/{environment_key}/queue-change",
        headers={"Authorization": f"Token {token}"},
        json={"updated_at": updated_at},
    )


def test_send_identity_update_message_make_correct_request(mocker, settings):
    # Given
    base_url = "http://localhost:8000"
    token = "token"
    identifier = "test_identity"
    environment_key = "test_environment"

    settings.SSE_SERVER_BASE_URL = base_url
    settings.SSE_AUTHENTICATION_TOKEN = token
    mocked_requests = mocker.patch("sse.tasks.requests")

    # When
    send_identity_update_message(environment_key, identifier)

    # Then
    mocked_requests.post.assert_called_once_with(
        f"{base_url}/sse/environments/{environment_key}/identities/queue-change",
        headers={"Authorization": f"Token {token}"},
        json={"identifier": identifier},
    )


def test_send_identity_update_messages_calls_singular_function_correctly(
    settings, mocker
):
    # Given
    environment_key = "test_environment"
    identifiers = ["test_identity_1", "test_identity_2"]

    mocked_send_identity_update_message = mocker.patch(
        "sse.tasks.send_identity_update_message"
    )

    # When
    send_identity_update_messages(environment_key, identifiers)

    # Then
    mocked_send_identity_update_message.has_calls(
        mocker.call(environment_key, identifiers[0]),
        mocker.call(environment_key, identifiers[1]),
    )


def test_auth_header_raises_exception_if_token_not_set(settings):
    # Given
    settings.SSE_AUTHENTICATION_TOKEN = None

    # When
    with pytest.raises(SSEAuthTokenNotSet):
        get_auth_header()
