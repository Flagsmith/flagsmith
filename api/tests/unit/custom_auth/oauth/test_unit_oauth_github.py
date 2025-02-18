from unittest import mock

import pytest

from custom_auth.oauth.exceptions import GithubError
from custom_auth.oauth.github import NON_200_ERROR_MESSAGE, GithubUser


@mock.patch("custom_auth.oauth.github.requests")
def test_get_access_token_success_with_oauth_github(
    mock_requests: mock.MagicMock,
) -> None:
    # Given
    test_code = "abc123"
    expected_access_token = "access-token"
    client_id = "test-client-id"
    client_secret = "test-client-secret"

    mock_requests.post.return_value = mock.MagicMock(
        text=f"access_token={expected_access_token}&scope=user&token_type=bearer",
        status_code=200,
    )

    # When
    github_user = GithubUser(
        test_code,
        client_id=client_id,
        client_secret=client_secret,
    )

    # Then
    assert github_user.access_token == expected_access_token

    assert mock_requests.post.call_count == 1
    request_calls = mock_requests.post.call_args
    assert request_calls[1]["data"]["code"] == test_code


@mock.patch("custom_auth.oauth.github.requests")
def test_get_access_token_fail_non_200_with_github_oauth(
    mock_requests: mock.MagicMock,
) -> None:
    # Given
    client_id = "test-client-id"
    client_secret = "test-client-secret"
    invalid_code = "invalid"
    status_code = 400
    mock_requests.post.return_value = mock.MagicMock(status_code=status_code)

    # When
    with pytest.raises(GithubError) as e:
        GithubUser(
            invalid_code,
            client_id=client_id,
            client_secret=client_secret,
        )

    # Then - exception raised
    assert NON_200_ERROR_MESSAGE.format(status_code) in str(e)


@mock.patch("custom_auth.oauth.github.requests")
def test_get_access_token_fail_token_expired_with_github_oauth(
    mock_requests: mock.MagicMock,
) -> None:
    # Given
    invalid_code = "invalid"
    client_id = "test-client-id"
    client_secret = "test-client-secret"

    error_description = "there+was+an+error"
    mock_requests.post.return_value = mock.MagicMock(
        text=f"error=bad_verification_code&error_description={error_description}",
        status_code=200,
    )

    # When
    with pytest.raises(GithubError) as e:
        GithubUser(
            invalid_code,
            client_id=client_id,
            client_secret=client_secret,
        )

    # Then
    assert error_description.replace("+", " ") in str(e)


@mock.patch("custom_auth.oauth.github.requests")
def test_get_user_name_and_id_with_github_oauth(mock_requests: mock.MagicMock) -> None:
    # Given
    # mock the post to get the access token
    mock_requests.post.return_value = mock.MagicMock(
        status_code=200, text="access_token=123456"
    )
    client_id = "test-client-id"
    client_secret = "test-client-secret"

    # mock the get to get the user info
    mock_response = mock.MagicMock(status_code=200)
    mock_requests.get.return_value = mock_response
    mock_response.json.return_value = {"name": "tommy tester", "id": 123456}

    # When
    github_user = GithubUser(
        "test-code",
        client_id=client_id,
        client_secret=client_secret,
    )
    user_name_and_id = github_user._get_user_name_and_id()  # type: ignore[no-untyped-call]

    # Then
    assert user_name_and_id == {
        "first_name": "tommy",
        "last_name": "tester",
        "github_user_id": 123456,
    }


@mock.patch("custom_auth.oauth.github.requests")
def test_get_primary_email_with_github_oauth(mock_requests: mock.MagicMock) -> None:
    # Given
    # mock the post to get the access token
    mock_requests.post.return_value = mock.MagicMock(
        status_code=200, text="access_token=123456"
    )
    client_id = "test-client-id"
    client_secret = "test-client-secret"

    # mock the request to get the user info
    mock_response = mock.MagicMock(status_code=200)
    mock_requests.get.return_value = mock_response

    verified_emails = [
        {
            "email": f"tommy_tester@example_{i}.com",
            "verified": True,
            "visibility": None,
            "primary": False,
        }
        for i in range(5)
    ]

    # set one of the verified emails to be the primary
    verified_emails[3]["primary"] = True

    mock_response.json.return_value = verified_emails

    # When
    github_user = GithubUser(
        "test-code",
        client_id=client_id,
        client_secret=client_secret,
    )
    primary_email = github_user._get_primary_email()  # type: ignore[no-untyped-call]

    # Then
    assert primary_email == verified_emails[3]["email"]
