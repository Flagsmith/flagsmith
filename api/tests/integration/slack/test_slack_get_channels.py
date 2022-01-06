from dataclasses import asdict

from django.urls import reverse
from rest_framework import status


def test_get_channels_returns_400_when_slack_project_config_does_not_exist(
    admin_client, environment, environment_api_key
):
    # Given
    url = reverse(
        "api-v1:environments:integrations-slack-channels-list",
        args=[environment_api_key],
    )

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        "Slack api token not found. Please generate the token using oauth"
        == response.json()["detail"]
    )


def test_get_channels_pagination(
    mocker,
    admin_client,
    environment_api_key,
    slack_project_config,
    slack_channels_data_response,
):
    # Given
    page_size = 10
    base_url = reverse(
        "api-v1:environments:integrations-slack-channels-list",
        args=[environment_api_key],
    )
    mocked_get_channels_data = mocker.patch(
        "integrations.slack.views.SlackWrapper.get_channels_data",
        return_value=slack_channels_data_response,
    )
    url = f"{base_url}?page_size={page_size}"

    # Let's make the first call
    response = admin_client.get(url)
    # and, verify that get_channels_data was called with correct arguments
    mocked_get_channels_data.assert_called_with(limit=page_size, cursor=None)

    # Next, verify the length of the result
    assert response.json()["count"] == len(slack_channels_data_response.channels)
    assert len(response.json()["results"]) == len(slack_channels_data_response.channels)

    # Now, let's make the second call using cursor
    cursor = response.json()["cursor"]
    url = f"{base_url}?cursor={cursor}?page_size={page_size}"
    response = admin_client.get(url)
    # Finally verify that get_channels_data was called with correct arguments
    mocked_get_channels_data.assert_called_with(cursor=cursor, limit=page_size)


def test_get_channels_response_structure(
    mocker,
    admin_client,
    environment_api_key,
    slack_project_config,
    slack_channels_data_response,
):
    # Given
    url = reverse(
        "api-v1:environments:integrations-slack-channels-list",
        args=[environment_api_key],
    )
    mocked_get_channels_data = mocker.patch(
        "integrations.slack.views.SlackWrapper.get_channels_data",
        return_value=slack_channels_data_response,
    )

    # When
    response = admin_client.get(url)

    # Then
    mocked_get_channels_data.assert_called()
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["cursor"] == slack_channels_data_response.cursor
    assert response.json()["results"][0] == asdict(
        slack_channels_data_response.channels[0]
    )
    assert response.json()["results"][1] == asdict(
        slack_channels_data_response.channels[1]
    )
