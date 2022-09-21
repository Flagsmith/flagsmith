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
