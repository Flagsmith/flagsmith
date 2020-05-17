from unittest import mock

from custom_auth.oauth.google import get_user_info, USER_INFO_URL


@mock.patch("custom_auth.oauth.google.requests")
def test_get_user_info(mock_requests):
    # Given
    access_token = "access-token"
    mock_google_response_data = {
        "id": "test-id",
        "given_name": "testy",
        "family_name": "tester",
        "email": "testytester@example.com"
    }
    expected_headers = {"Authorization": f"Bearer {access_token}"}
    mock_response = mock.MagicMock()
    mock_requests.get.return_value = mock_response
    mock_response.json.return_value = mock_google_response_data

    # When
    response = get_user_info(access_token)

    # Then
    mock_requests.get.assert_called_with(USER_INFO_URL, headers=expected_headers)
    assert response == {
        "email": mock_google_response_data["email"],
        "first_name": mock_google_response_data["given_name"],
        "last_name": mock_google_response_data["family_name"],
        "google_user_id": mock_google_response_data["id"]
    }