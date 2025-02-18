import json

import pytest
from django.urls import reverse

from integrations.slack.slack import ChannelsDataResponse, SlackChannel


@pytest.fixture
def slack_bot_token():  # type: ignore[no-untyped-def]
    return "bot_token_test"


@pytest.fixture
def slack_channels_data_response():  # type: ignore[no-untyped-def]
    channels = [SlackChannel("name1", "id1"), SlackChannel("name2", "id2")]
    return ChannelsDataResponse(channels=channels, cursor="test_cursor")


@pytest.fixture
def slack_project_config(  # type: ignore[no-untyped-def]
    mocker, django_client, environment, environment_api_key, slack_bot_token
):
    url = reverse(
        "api-v1:environments:integrations-slack-slack-oauth-callback",
        args=[environment_api_key],
    )
    mocker.patch(
        "integrations.slack.views.SlackWrapper.get_bot_token",
        return_value=slack_bot_token,
    )
    mocker.patch(
        "integrations.slack.views.SlackEnvironmentViewSet._get_front_end_redirect_url",
        return_value="http://localhost",
    )
    mocker.patch("integrations.slack.views.validate_state", return_value=True)
    django_client.get(f"{url}?state=state&code=code")


@pytest.fixture
def slack_environment_config(  # type: ignore[no-untyped-def]
    mocker, admin_client, environment, environment_api_key, slack_project_config
):
    url = reverse(
        "api-v1:environments:integrations-slack-list",
        args=[environment_api_key],
    )
    env_config = {"channel_id": "channel_id1", "enabled": True}
    mocker.patch("integrations.slack.serializers.SlackWrapper.join_channel")
    response = admin_client.post(
        url,
        data=json.dumps(env_config),
        content_type="application/json",
    )
    return response.json()["id"]


@pytest.fixture
def mocked_slack_wrapper(mocker):  # type: ignore[no-untyped-def]
    return mocker.patch("integrations.slack.views.SlackWrapper")
