import json

import pytest
from django.urls import reverse
from rest_framework import status

bot_token = "bot_token_test"


@pytest.fixture
def slack_project_config(mocker, django_client, environment, environment_api_key):
    url = reverse(
        "api-v1:environments:integrations-slack-slack-oauth-callback",
        args=[environment_api_key],
    )
    mocker.patch("integrations.slack.views.get_bot_token", return_value=bot_token)
    mocker.patch("integrations.slack.views.validate_state", return_value=True)
    django_client.get(f"{url}?state=state&code=code")


@pytest.fixture
def slack_environment_config(
    mocker, admin_client, environment, environment_api_key, slack_project_config
):
    url = reverse(
        "api-v1:environments:integrations-slack-list",
        args=[environment_api_key],
    )
    env_config = {"channel_id": "channel_id1", "enabled": True}
    mocker.patch("integrations.slack.models.join_channel")
    response = admin_client.post(
        url,
        data=json.dumps(env_config),
        content_type="application/json",
    )
    return response.json()["id"]


def test_get_channels_returns_400_when_slack_project_config_does_not_exist(
    admin_client, environment, environment_api_key
):
    # Given
    url = reverse(
        "api-v1:environments:integrations-slack-get-channels",
        args=[environment_api_key],
    )

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Slack api token not found" in response.json()


def test_get_channels_returns_200_when_slack_project_config_exists(
    mocker, admin_client, environment_api_key, slack_project_config
):
    # Given
    url = reverse(
        "api-v1:environments:integrations-slack-get-channels",
        args=[environment_api_key],
    )
    channels_data = [{"channel_name": "test_channel", "channel_id": "123"}]
    mocked_get_channels_data = mocker.patch(
        "integrations.slack.views.get_channels_data", return_value=channels_data
    )

    # When
    response = admin_client.get(url)

    # Then
    mocked_get_channels_data.assert_called_with(bot_token)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == channels_data


def test_posting_env_config_return_400_when_slack_project_config_does_not_exist(
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


def test_posting_env_config_calls_join_channel(
    mocker, admin_client, environment, environment_api_key, slack_project_config
):
    # Given
    url = reverse(
        "api-v1:environments:integrations-slack-list",
        args=[environment_api_key],
    )
    env_config = {"channel_id": "channel_id1", "enabled": True}
    mocked_join_channel = mocker.patch("integrations.slack.models.join_channel")

    # When
    response = admin_client.post(
        url,
        data=json.dumps(env_config),
        content_type="application/json",
    )

    # Then
    mocked_join_channel.assert_called_with(bot_token, env_config["channel_id"])
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["enabled"] == env_config["enabled"]
    assert response.json()["channel_id"] == env_config["channel_id"]


def test_update_environment_config_calls_join_channel(
    mocker, admin_client, environment, environment_api_key, slack_environment_config
):
    # Given
    url = reverse(
        "api-v1:environments:integrations-slack-detail",
        args=[environment_api_key, slack_environment_config],
    )
    env_config = {"channel_id": "channel_id2", "enabled": True}
    mocked_join_channel = mocker.patch("integrations.slack.models.join_channel")

    # When
    response = admin_client.put(
        url,
        data=json.dumps(env_config),
        content_type="application/json",
    )

    # Then
    mocked_join_channel.assert_called_with(bot_token, env_config["channel_id"])
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["enabled"] == env_config["enabled"]
    assert response.json()["channel_id"] == env_config["channel_id"]


def test_get_environment_config_list_returns_200(
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


def test_get_environment_config_returns_200(
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
