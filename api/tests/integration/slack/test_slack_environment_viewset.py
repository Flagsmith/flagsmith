import json

from django.urls import reverse
from rest_framework import status

from integrations.slack.exceptions import SlackChannelJoinError


def test_posting_env_config_return_400_when_slack_project_config_does_not_exist(  # type: ignore[no-untyped-def]
    admin_client, environment, environment_api_key
):
    # Given
    url = reverse(
        "api-v1:environments:integrations-slack-list",
        args=[environment_api_key],
    )
    # When
    response = admin_client.post(
        url,
        data=json.dumps({"channel_id": "test_id", "enabled": True}),
        content_type="application/json",
    )
    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Slack api token not found" in response.json()[0]


def test_posting_env_config_calls_join_channel(  # type: ignore[no-untyped-def]
    mocker,
    admin_client,
    environment,
    environment_api_key,
    slack_project_config,
    slack_bot_token,
):
    # Given
    url = reverse(
        "api-v1:environments:integrations-slack-list",
        args=[environment_api_key],
    )
    env_config = {"channel_id": "channel_id1", "enabled": True}
    mocked_slack_wrapper = mocker.patch("integrations.slack.serializers.SlackWrapper")
    # When
    response = admin_client.post(
        url,
        data=json.dumps(env_config),
        content_type="application/json",
    )

    # Then
    mocked_slack_wrapper.assert_called_with(
        api_token=slack_bot_token, channel_id=env_config["channel_id"]
    )
    mocked_slack_wrapper.return_value.join_channel.assert_called_with()
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["enabled"] == env_config["enabled"]
    assert response.json()["channel_id"] == env_config["channel_id"]


def test_update_environment_config_calls_join_channel(  # type: ignore[no-untyped-def]
    mocker,
    admin_client,
    environment,
    environment_api_key,
    slack_environment_config,
    slack_bot_token,
):
    # Given
    url = reverse(
        "api-v1:environments:integrations-slack-detail",
        args=[environment_api_key, slack_environment_config],
    )
    env_config = {"channel_id": "channel_id2", "enabled": True}

    mocked_slack_wrapper = mocker.patch("integrations.slack.serializers.SlackWrapper")

    # When
    response = admin_client.put(
        url,
        data=json.dumps(env_config),
        content_type="application/json",
    )

    # Then
    mocked_slack_wrapper.assert_called_with(
        api_token=slack_bot_token, channel_id=env_config["channel_id"]
    )
    mocked_slack_wrapper.return_value.join_channel.assert_called_with()

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["enabled"] == env_config["enabled"]
    assert response.json()["channel_id"] == env_config["channel_id"]


def test_update_environment_config_returns_400_if_join_channel_raises_slack_channel_join_error(  # type: ignore[no-untyped-def]  # noqa: E501
    mocker,
    admin_client,
    environment,
    environment_api_key,
    slack_environment_config,
    slack_bot_token,
):
    # Given
    slack_error_code = "some_slack_error_code"
    url = reverse(
        "api-v1:environments:integrations-slack-detail",
        args=[environment_api_key, slack_environment_config],
    )
    env_config = {"channel_id": "channel_id2", "enabled": True}

    mocked_slack_wrapper = mocker.patch("integrations.slack.serializers.SlackWrapper")
    mocked_slack_wrapper.return_value.join_channel.side_effect = SlackChannelJoinError(
        slack_error_code
    )
    # When
    response = admin_client.put(
        url,
        data=json.dumps(env_config),
        content_type="application/json",
    )

    # Then
    mocked_slack_wrapper.assert_called_with(
        api_token=slack_bot_token, channel_id=env_config["channel_id"]
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()[0] == slack_error_code


def test_get_environment_config_list_returns_200(  # type: ignore[no-untyped-def]
    admin_client, environment, environment_api_key, slack_environment_config
):
    # Given
    url = reverse(
        "api-v1:environments:integrations-slack-list",
        args=[environment_api_key],
    )
    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == slack_environment_config


def test_get_environment_config_returns_200(  # type: ignore[no-untyped-def]
    admin_client, environment, environment_api_key, slack_environment_config
):
    # Given
    url = reverse(
        "api-v1:environments:integrations-slack-detail",
        args=[environment_api_key, slack_environment_config],
    )
    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == slack_environment_config
