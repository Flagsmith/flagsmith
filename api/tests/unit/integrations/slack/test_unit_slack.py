import pytest

from integrations.slack.slack import SlackWrapper


@pytest.fixture
def mocked_slack_internal_client(mocker):
    mocked_client = mocker.MagicMock()

    mocker.patch(
        "integrations.slack.slack.SlackWrapper._client",
        new_callable=mocker.PropertyMock,
        return_value=mocked_client,
    )
    return mocked_client


def test_get_channels_data_response_structure(mocker, mocked_slack_internal_client):
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
    mocked_slack_internal_client.conversations_list.return_value = response_data
    channels = SlackWrapper(api_token=api_token).get_channels_data()

    # Then
    assert channels == [
        {"channel_name": "channel1", "channel_id": "id1"},
        {"channel_name": "channel2", "channel_id": "id2"},
    ]

    mocked_slack_internal_client.conversations_list.assert_called_with(
        exclude_archived=True
    )


def test_client_makes_correct_calls(mocker):
    # Given
    api_token = "random_token"

    mocked_web_client = mocker.patch("integrations.slack.slack.WebClient")

    # When
    slack_wrapper = SlackWrapper(api_token=api_token)

    # Then
    assert mocked_web_client.return_value == slack_wrapper._client
    mocked_web_client.assert_called_with(token=api_token)


def test_join_channel_makes_correct_call(mocker, mocked_slack_internal_client):
    # Given
    channel = "channel_1"
    api_token = "random_token"

    # When
    SlackWrapper(api_token=api_token, channel_id=channel).join_channel()

    # Then
    mocked_slack_internal_client.conversations_join.assert_called_with(channel=channel)


def test_get_bot_token_makes_correct_calls(
    mocker, settings, mocked_slack_internal_client
):
    # Given
    code = "test_code"
    redirect_uri = "http://localhost"
    settings.SLACK_CLIENT_ID = "test_client_id"
    settings.SLACK_CLIENT_SECRET = "test_client_secret"

    slack_wrapper = SlackWrapper()

    # When
    token = slack_wrapper.get_bot_token(code, redirect_uri)

    # Then
    mocked_slack_internal_client.oauth_v2_access.assert_called_with(
        client_id=settings.SLACK_CLIENT_ID,
        client_secret=settings.SLACK_CLIENT_SECRET,
        code=code,
        redirect_uri=redirect_uri,
    )
    assert (
        token
        == mocked_slack_internal_client.oauth_v2_access.return_value.get.return_value
    )


def test_slack_initialized_correctly(mocker, mocked_slack_internal_client):
    # Given
    api_token = "test_token"
    channel_id = "channel_id_1"

    # When
    slack_wrapper = SlackWrapper(api_token, channel_id)

    # Then
    assert slack_wrapper.channel_id == channel_id
    assert slack_wrapper._client == mocked_slack_internal_client


def test_track_event_makes_correct_call(mocker, mocked_slack_internal_client):
    # Given
    api_token = "test_token"
    channel_id = "channel_id_1"
    event = {"text": "random_text"}

    slack_wrapper = SlackWrapper(api_token, channel_id)

    # When
    slack_wrapper._track_event(event)

    # Then
    mocked_slack_internal_client.chat_postMessage.assert_called_with(
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
