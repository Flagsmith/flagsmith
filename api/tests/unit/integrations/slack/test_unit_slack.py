from unittest import mock

from integrations.slack.slack import get_channels_data


def test_get_channels_data_repsonse_structure():
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
        response = get_channels_data(api_token)

    # Then
    assert response == [
        {"channel_name": "channel1", "channel_id": "id1"},
        {"channel_name": "channel2", "channel_id": "id2"},
    ]
    client.assert_called_with(api_token)
    client.return_value.conversations_list.assert_called_with(exclude_archived=True)
