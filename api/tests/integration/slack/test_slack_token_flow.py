from urllib.parse import parse_qs, urlparse

from django.urls import reverse
from rest_framework import status


def test_slack_oauth_flow(
    mocker, settings, admin_client, environment_api_key, environment
):
    # Given
    settings.SLACK_CLIENT_ID = "slack_id"
    settings.SLACK_CLIENT_SECRET = "client_secret"

    # Let's start the oauth flow
    url = reverse(
        "api-v1:environments:integrations-slack-slack-oauth-init",
        args=[environment_api_key],
    )
    response = admin_client.get(url)

    # Verify the response
    assert response.status_code == status.HTTP_302_FOUND
    params = parse_qs(urlparse(response.url).query)
    state = params["state"][0]
    assert params["client_id"][0] == settings.SLACK_CLIENT_ID
    mocked_get_bot_token = mocker.MagicMock(return_value="bot_token")
    mocked_slack_wrapper = mocker.patch("integrations.slack.views.SlackWrapper")
    mocked_slack_wrapper.return_value.get_bot_token = mocked_get_bot_token

    # Now, let's hit the callback uri
    callback_url = params["redirect_uri"][0]
    code = "random_slack_code"

    # Add state and code to the callback url
    response = admin_client.get(f"{callback_url}?state={state}&code={code}")
    assert response.status_code == status.HTTP_204_NO_CONTENT
    # Finally, verify that get_bot_token was called with correct arguments
    mocked_slack_wrapper.assert_called_with(code, callback_url)
    mocked_get_bot_token.assert_called_with()
