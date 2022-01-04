from urllib.parse import parse_qs, urlparse

from django.urls import reverse
from rest_framework import status


def test_slack_oauth_flow(
    mocker, settings, admin_client, environment_api_key, environment
):
    # Given
    settings.SLACK_CLIENT_ID = "slack_id"
    settings.SLACK_CLIENT_SECRET = "client_secret"

    redirect_url = "http://localhost"
    # First, let's fetch the signature
    url = reverse(
        "api-v1:environments:integrations-slack-get-temporary-signature",
        args=[environment_api_key],
    )
    signature = admin_client.get(url).json()["signature"]
    # Now, Let's start the oauth flow
    base_url = reverse(
        "api-v1:environments:integrations-slack-slack-oauth-init",
        args=[environment_api_key],
    )
    url = f"{base_url}?redirect_url={redirect_url}&signature={signature}"
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
    # verity that the redirect worked correctly
    assert response.status_code == status.HTTP_302_FOUND
    assert response.url == redirect_url
    # Finally, verify that get_bot_token was called with correct arguments
    mocked_slack_wrapper.assert_called_with()
    mocked_get_bot_token.assert_called_with(code, callback_url)


def test_slack_oauth_callback_returns_400_if_redirect_url_is_not_found_in_session(
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

    mocker.patch("integrations.slack.views.validate_state", return_value=True)
    response = django_client.get(f"{url}?state=state&code=code")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Redirect URL not found in request session"


def test_slack_oauth_init_returns_400_for_invalid_signature(
    django_client, environment, environment_api_key, settings
):
    # Given
    settings.SLACK_CLIENT_ID = "slack_id"
    settings.SLACK_CLIENT_SECRET = "client_secret"

    base_url = reverse(
        "api-v1:environments:integrations-slack-slack-oauth-init",
        args=[environment_api_key],
    )
    url = f"{base_url}?redirect_url=http://localhost&signature=random_sign"
    response = django_client.get(url)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Invalid or expired signature"
