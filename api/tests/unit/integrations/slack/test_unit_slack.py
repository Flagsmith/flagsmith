import pytest
from slack_sdk.errors import SlackApiError

from audit.models import AuditLog
from environments.models import Environment
from integrations.slack.exceptions import SlackChannelJoinError
from integrations.slack.slack import SlackChannel, SlackWrapper


def test_get_channels_data__valid_response__returns_correct_structure(  # type: ignore[no-untyped-def]
    mocker, mocked_slack_internal_client
):
    # Given
    api_token = "test_token"
    cursor = "dGVhbTpDMDI3MEpNRldNVg=="
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
        "response_metadata": {"next_cursor": cursor},
    }

    # When
    some_kwargs = {"key": "value"}
    mocked_slack_internal_client.conversations_list.return_value = response_data
    channels_data = SlackWrapper(api_token=api_token).get_channels_data(**some_kwargs)

    # Then
    assert channels_data.channels == [
        SlackChannel("channel1", "id1"),
        SlackChannel("channel2", "id2"),
    ]
    assert channels_data.cursor == cursor

    mocked_slack_internal_client.conversations_list.assert_called_with(
        exclude_archived=True, **some_kwargs
    )


def test_slack_wrapper__init_with_token__creates_web_client_correctly(mocker):  # type: ignore[no-untyped-def]
    # Given
    api_token = "random_token"

    mocked_web_client = mocker.patch("integrations.slack.slack.WebClient")

    # When
    slack_wrapper = SlackWrapper(api_token=api_token)

    # Then
    assert mocked_web_client.return_value == slack_wrapper._client
    mocked_web_client.assert_called_with(token=api_token)


def test_join_channel__valid_channel__calls_conversations_join(  # type: ignore[no-untyped-def]
    mocker, mocked_slack_internal_client
):
    # Given
    channel = "channel_1"
    api_token = "random_token"

    # When
    SlackWrapper(api_token=api_token, channel_id=channel).join_channel()  # type: ignore[no-untyped-call]

    # Then
    mocked_slack_internal_client.conversations_join.assert_called_with(channel=channel)


def test_join_channel__slack_api_error__raises_slack_channel_join_error(  # type: ignore[no-untyped-def]
    mocker, mocked_slack_internal_client
):
    # Given
    channel = "channel_1"
    api_token = "random_token"
    mocked_slack_internal_client.conversations_join.side_effect = SlackApiError(  # type: ignore[no-untyped-call]
        message="server_error", response={"error": "some_error_code"}
    )
    # When / Then
    with pytest.raises(SlackChannelJoinError):
        SlackWrapper(api_token=api_token, channel_id=channel).join_channel()  # type: ignore[no-untyped-call]


def test_get_bot_token__valid_code__calls_oauth_and_returns_token(  # type: ignore[no-untyped-def]
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


def test_slack_wrapper__token_and_channel__initialises_correctly(  # type: ignore[no-untyped-def]
    mocker, mocked_slack_internal_client
):
    # Given
    api_token = "test_token"
    channel_id = "channel_id_1"

    # When
    slack_wrapper = SlackWrapper(api_token, channel_id)

    # Then
    assert slack_wrapper.channel_id == channel_id
    assert slack_wrapper._client == mocked_slack_internal_client


def test_track_event__valid_event__calls_chat_post_message(  # type: ignore[no-untyped-def]
    mocked_slack_internal_client,
):
    # Given
    api_token = "test_token"
    channel_id = "channel_id_1"
    event = {"blocks": []}  # type: ignore[var-annotated]

    slack_wrapper = SlackWrapper(api_token, channel_id)

    # When
    slack_wrapper._track_event(event)

    # Then
    mocked_slack_internal_client.chat_postMessage.assert_called_with(
        channel=channel_id, blocks=event["blocks"]
    )


def test_generate_event_data__audit_log_record__returns_correct_blocks(  # type: ignore[no-untyped-def]
    django_user_model,
):
    # Given
    log = "some log data"

    author = django_user_model(email="test@email.com")
    environment = Environment(name="test")

    audit_log_record = AuditLog(log=log, author=author, environment=environment)

    # When
    event_data = SlackWrapper.generate_event_data(audit_log_record=audit_log_record)

    # Then
    assert event_data["blocks"] == [
        {"type": "section", "text": {"type": "plain_text", "text": log}},
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Environment:*\n{environment.name}"},
                {"type": "mrkdwn", "text": f"*User:*\n{author.email}"},
            ],
        },
    ]
