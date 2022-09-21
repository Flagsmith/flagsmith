from realtime.service import (
    send_environment_update_messages,
    send_identity_update_message,
)


def test_send_environment_update_messages_returns_without_request_if_not_configured(
    mocker, settings
):
    # Given
    mocked_requests = mocker.patch("realtime.service.requests")

    # When
    send_environment_update_messages(["environment_key"])

    # Then
    mocked_requests.post.assert_not_called()


def test_identity_update_message_returns_without_request_if_not_configured(
    mocker, settings
):
    # Given
    mocked_requests = mocker.patch("realtime.service.requests")

    # When
    send_identity_update_message("environment_key", "identity_key")

    # Then
    mocked_requests.post.assert_not_called()


def test_send_environment_update_messages_make_correct_request(mocker, settings):
    # Given
    base_url = "http://localhost:8000"
    token = "token"
    environment_keys = ["test_environment_1", "test_environment_2"]

    settings.SSE_SERVER_BASE_URL = base_url
    settings.SSE_AUTHENTICATION_TOKEN = token
    mocked_requests = mocker.patch("realtime.service.requests")

    # When
    send_environment_update_messages(environment_keys)

    # Then
    mocked_requests.post.has_calls(
        mocker.call(
            f"{base_url}/sse/environments/{environment_keys[0]}/queue-change",
            headers={"Authorization": f"Token {token}"},
        ),
        mocker.call(
            f"{base_url}/sse/environments/{environment_keys[1]}/queue-change",
            headers={"Authorization": f"Token {token}"},
        ),
    )


def test_send_identity_update_message_make_correct_request(mocker, settings):
    # Given
    base_url = "http://localhost:8000"
    token = "token"
    identifier = "test_identity"
    environment_key = "test_environment"

    settings.SSE_SERVER_BASE_URL = base_url
    settings.SSE_AUTHENTICATION_TOKEN = token
    mocked_requests = mocker.patch("realtime.service.requests")

    # When
    send_identity_update_message(environment_key, identifier)

    # Then
    mocked_requests.post.assert_called_once_with(
        f"{base_url}/sse/environments/{environment_key}/identities/queue-change",
        headers={"Authorization": f"Token {token}"},
        json={"identifier": identifier},
    )
