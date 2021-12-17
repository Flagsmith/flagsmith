from unittest import mock

import pytest

from integrations.slack.slack import (
    SlackWrapper,
    get_bot_token,
    get_channels_data,
    get_client,
    join_channel,
)


@pytest.fixture()
def mocked_get_client(mocker):
    return mocker.patch("integrations.slack.slack.get_client")


def test_get_channels_data_response_structure():
    # Given
    api_token = "test_token"
    response_data = {
        "ok": True,
        "channels": [
            {
                "id": "id1",
                "name": "channel1",
                "is_channel": True,
                "num_members": 3,
            },
            {
                "id": "id2",
                "name": "channel2",
                "is_channel": True,
                "num_members": 3,
            },
        ],
        "response_metadata": {"next_cursor": "dGVhbTpDMDI3MEpNRldNVg=="},
    }

    # When
    with mock.patch("integrations.slack.slack.get_client") as client:
        client.return_value.conversations_list.return_value = response_data
        channels = get_channels_data(api_token)

    # Then
    assert channels == [
        {"channel_name": "channel1", "channel_id": "id1"},
        {"channel_name": "channel2", "channel_id": "id2"},
    ]
    client.assert_called_with(api_token)
    client.return_value.conversations_list.assert_called_with(exclude_archived=True)


def test_get_client_makes_correct_calls(mocker):
    # Given
    api_token = "random_token"

    mocked_web_client = mocker.patch("integrations.slack.slack.WebClient")

    # When
    client = get_client(api_token)

    # Then
    assert mocked_web_client.return_value == client
    mocked_web_client.assert_called_with(token=api_token)


def test_join_channel_makes_correct_call(mocker):
    # Given
    channel = "channel_1"
    api_token = "random_token"
    mocked_client = mocker.MagicMock()
    mocked_get_client = mocker.patch(
        "integrations.slack.slack.get_client", return_value=mocked_client
    )

    # When
    join_channel(api_token, channel)

    # Then
    mocked_get_client.assert_called_with(api_token)
    mocked_client.conversations_join.assert_called_with(channel=channel)


def test_get_bot_token_makes_correct_calls(mocker, settings, mocked_get_client):
    # Given
    code = "test_code"
    redirect_uri = "http://localhost"
    settings.SLACK_CLIENT_ID = "test_client_id"
    settings.SLACK_CLIENT_SECRET = "test_client_secret"

    mocked_client = mocker.MagicMock()
    mocked_get_client.return_value = mocked_client
    # When
    token = get_bot_token(code, redirect_uri)

    # Then
    mocked_get_client.assert_called_with()
    mocked_client.oauth_v2_access.assert_called_with(
        client_id=settings.SLACK_CLIENT_ID,
        client_secret=settings.SLACK_CLIENT_SECRET,
        code=code,
        redirect_uri=redirect_uri,
    )
    assert token == mocked_client.oauth_v2_access.return_value.get.return_value


def test_slack_initialized_correctly(mocker, mocked_get_client):
    # Given
    api_token = "test_token"
    channel_id = "channel_id_1"

    # When
    slack_wrapper = SlackWrapper(api_token, channel_id)
    assert slack_wrapper.channel_id == channel_id
    assert slack_wrapper.client == mocked_get_client.return_value

    # Then
    mocked_get_client.assert_called_with(api_token)


def test_track_event_makes_correct_call(mocker, mocked_get_client):
    # Given
    api_token = "test_token"
    channel_id = "channel_id_1"
    event = {"text": "random_text"}

    mocked_client = mocker.MagicMock()
    mocked_get_client.return_value = mocked_client

    slack_wrapper = SlackWrapper(api_token, channel_id)

    # When
    slack_wrapper._track_event(event)

    # Then
    mocked_client.chat_postMessage.assert_called_with(
        channel=channel_id, text=event["text"]
    )


def test_slack_generate_event_data_with_correct_values():
    # Given
    log = "some log data"
    email = "tes@email.com"
    environment_name = "test"
    # When
    event_data = SlackWrapper.generate_event_data(log, email, environment_name)

    assert event_data["title"] == "Flagsmith Feature Flag Event"
    assert event_data["text"] == f"{log} by user {email}"
    assert event_data["tags"] == [f"env:{environment_name}"]
