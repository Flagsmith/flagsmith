from typing import Any
from unittest import mock

from django.db.models import Model
from django.test import override_settings
from django.urls import reverse
from pytest_mock import MockerFixture
from rest_framework import status
from rest_framework.test import APIClient

from organisations.invites.models import Invite
from organisations.models import Organisation
from users.models import SignUpType


@mock.patch("custom_auth.oauth.serializers.get_user_info")
@override_settings(ALLOW_REGISTRATION_WITHOUT_INVITE=False)
def test_cannot_register_with_google_without_invite_if_registration_disabled(  # type: ignore[no-untyped-def]
    mock_get_user_info, db
):
    # Given
    url = reverse("api-v1:custom_auth:oauth:google-oauth-login")
    client = APIClient()

    email = "test@example.com"
    mock_get_user_info.return_value = {"email": email}

    # When
    response = client.post(url, data={"access_token": "some-token"})

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


@mock.patch("custom_auth.oauth.serializers.GithubUser")
@override_settings(ALLOW_REGISTRATION_WITHOUT_INVITE=False)
def test_cannot_register_with_github_without_invite_if_registration_disabled(  # type: ignore[no-untyped-def]
    MockGithubUser, db
):
    # Given
    url = reverse("api-v1:custom_auth:oauth:github-oauth-login")
    client = APIClient()

    email = "test@example.com"
    mock_github_user = mock.MagicMock()
    MockGithubUser.return_value = mock_github_user
    mock_github_user.get_user_info.return_value = {"email": email}

    # When
    response = client.post(url, data={"access_token": "some-token"})

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


@mock.patch("custom_auth.oauth.serializers.get_user_info")
@override_settings(ALLOW_REGISTRATION_WITHOUT_INVITE=False)
def test_can_register_with_google_with_invite_if_registration_disabled(  # type: ignore[no-untyped-def]
    mock_get_user_info, db
):
    # Given
    url = reverse("api-v1:custom_auth:oauth:google-oauth-login")
    client = APIClient()

    email = "test@example.com"
    mock_get_user_info.return_value = {"email": email}
    organisation = Organisation.objects.create(name="Test Org")
    Invite.objects.create(organisation=organisation, email=email)

    # When
    response = client.post(
        url,
        data={
            "access_token": "some-token",
            "sign_up_type": SignUpType.INVITE_EMAIL.value,
        },
    )

    # Then
    assert response.status_code == status.HTTP_200_OK


@mock.patch("custom_auth.oauth.serializers.GithubUser")
@override_settings(ALLOW_REGISTRATION_WITHOUT_INVITE=False)
def test_can_register_with_github_with_invite_if_registration_disabled(  # type: ignore[no-untyped-def]
    MockGithubUser, db
):
    # Given
    url = reverse("api-v1:custom_auth:oauth:github-oauth-login")
    client = APIClient()

    email = "test@example.com"
    mock_github_user = mock.MagicMock()
    MockGithubUser.return_value = mock_github_user
    mock_github_user.get_user_info.return_value = {"email": email}
    organisation = Organisation.objects.create(name="Test Org")
    Invite.objects.create(organisation=organisation, email=email)

    # When
    response = client.post(
        url,
        data={
            "access_token": "some-token",
            "sign_up_type": SignUpType.INVITE_EMAIL.value,
        },
    )

    # Then
    assert response.status_code == status.HTTP_200_OK


@mock.patch("custom_auth.oauth.serializers.get_user_info")
@override_settings(ALLOW_OAUTH_REGISTRATION_WITHOUT_INVITE=False)
def test_can_login_with_google_if_registration_disabled(  # type: ignore[no-untyped-def]
    mock_get_user_info, db, django_user_model
):
    # Given
    url = reverse("api-v1:custom_auth:oauth:google-oauth-login")
    client = APIClient()

    email = "test@example.com"
    mock_get_user_info.return_value = {
        "email": email,
        "first_name": "John",
        "last_name": "Smith",
        "google_user_id": "abc123",
    }
    django_user_model.objects.create(email=email)

    # When
    response = client.post(url, data={"access_token": "some-token"})

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert "key" in response.json()


@mock.patch("custom_auth.oauth.serializers.GithubUser")
@override_settings(ALLOW_OAUTH_REGISTRATION_WITHOUT_INVITE=False)
def test_can_login_with_github_if_registration_disabled(  # type: ignore[no-untyped-def]
    MockGithubUser, db, django_user_model
):
    # Given
    url = reverse("api-v1:custom_auth:oauth:github-oauth-login")
    client = APIClient()

    email = "test@example.com"
    mock_github_user = mock.MagicMock()
    MockGithubUser.return_value = mock_github_user
    mock_github_user.get_user_info.return_value = {
        "email": email,
        "first_name": "John",
        "last_name": "Smith",
        "github_user_id": "abc123",
    }
    django_user_model.objects.create(email=email)

    # When
    response = client.post(url, data={"access_token": "some-token"})

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert "key" in response.json()


def test_login_with_google_updates_existing_user_case_insensitive(
    db: None,
    django_user_model: type[Model],
    mocker: MockerFixture,
    api_client: APIClient,
) -> None:
    # Given
    email_lower = "test@example.com"
    email_upper = email_lower.upper()
    google_user_id = "abc123"

    django_user_model.objects.create(email=email_lower)  # type: ignore[attr-defined]

    mocker.patch(
        "custom_auth.oauth.serializers.get_user_info",
        return_value={
            "email": email_upper,
            "first_name": "John",
            "last_name": "Smith",
            "google_user_id": google_user_id,
        },
    )

    url = reverse("api-v1:custom_auth:oauth:google-oauth-login")

    # When
    response = api_client.post(url, data={"access_token": "some-token"})

    # Then
    assert response.status_code == status.HTTP_200_OK

    qs = django_user_model.objects.filter(email__iexact=email_lower)  # type: ignore[attr-defined]
    assert qs.count() == 1

    user = qs.first()
    assert user.email == email_lower
    assert user.google_user_id == google_user_id


def test_login_with_github_updates_existing_user_case_insensitive(
    db: None,
    django_user_model: type[Model],
    mocker: MockerFixture,
    api_client: APIClient,
) -> None:
    # Given
    email_lower = "test@example.com"
    email_upper = email_lower.upper()
    github_user_id = "abc123"

    django_user_model.objects.create(email=email_lower)  # type: ignore[attr-defined]

    mock_github_user = mock.MagicMock()
    mocker.patch(
        "custom_auth.oauth.serializers.GithubUser", return_value=mock_github_user
    )
    mock_github_user.get_user_info.return_value = {
        "email": email_upper,
        "first_name": "John",
        "last_name": "Smith",
        "github_user_id": github_user_id,
    }

    url = reverse("api-v1:custom_auth:oauth:github-oauth-login")

    # When
    response = api_client.post(url, data={"access_token": "some-token"})

    # Then
    assert response.status_code == status.HTTP_200_OK

    qs = django_user_model.objects.filter(email__iexact=email_lower)  # type: ignore[attr-defined]
    assert qs.count() == 1

    user = qs.first()
    assert user.email == email_lower
    assert user.github_user_id == github_user_id


def test_user_with_duplicate_accounts_authenticates_as_the_correct_oauth_user(
    db: None,
    django_user_model: type[Model],
    api_client: APIClient,
    mocker: MockerFixture,
) -> None:
    """
    Specific test to verify the correct behaviour for users affected by
    https://github.com/Flagsmith/flagsmith/issues/4185.
    """

    # Given
    email_lower = "test@example.com"
    email_upper = email_lower.upper()

    github_user = django_user_model.objects.create(  # type: ignore[attr-defined]
        email=email_lower, github_user_id="abc123"
    )
    google_user = django_user_model.objects.create(  # type: ignore[attr-defined]
        email=email_upper, google_user_id="abc123"
    )

    mock_github_user = mock.MagicMock()
    mocker.patch(
        "custom_auth.oauth.serializers.GithubUser", return_value=mock_github_user
    )
    mock_github_user.get_user_info.return_value = {
        "email": email_lower,
        "first_name": "John",
        "last_name": "Smith",
        "github_user_id": github_user.github_user_id,
    }

    mocker.patch(
        "custom_auth.oauth.serializers.get_user_info",
        return_value={
            "email": email_upper,
            "first_name": "John",
            "last_name": "Smith",
            "google_user_id": google_user.google_user_id,
        },
    )

    github_auth_url = reverse("api-v1:custom_auth:oauth:github-oauth-login")
    google_auth_url = reverse("api-v1:custom_auth:oauth:google-oauth-login")

    # When
    auth_with_github_response = api_client.post(
        github_auth_url, data={"access_token": "some-token"}
    )
    auth_with_google_response = api_client.post(
        google_auth_url, data={"access_token": "some-token"}
    )

    # Then
    github_auth_key = auth_with_github_response.json().get("key")
    assert github_auth_key == github_user.auth_token.key

    google_auth_key = auth_with_google_response.json().get("key")
    assert google_auth_key == google_user.auth_token.key


@mock.patch("custom_auth.oauth.serializers.get_user_info")
@override_settings(COOKIE_AUTH_ENABLED=True)
def test_login_with_google_jwt_cookie(
    mock_get_user_info: mock.Mock,
    db: None,
    django_user_model: type[Any],
    api_client: APIClient,
) -> None:
    # Given
    email = "test@example.com"
    google_user_id = "abc123"

    django_user_model.objects.create(email=email)
    mock_get_user_info.return_value = {
        "email": email,
        "first_name": "John",
        "last_name": "Smith",
        "google_user_id": google_user_id,
    }

    url = reverse("api-v1:custom_auth:oauth:google-oauth-login")

    # When
    response = api_client.post(url, data={"access_token": "some-token"})

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert response.cookies.get["jwt"]["httponly"]

    assert not response.data


@override_settings(COOKIE_AUTH_ENABLED=True)
def test_login_with_github_jwt_cookie(
    db: None,
    django_user_model: type[Any],
    api_client: APIClient,
    mocker: MockerFixture,
) -> None:
    # Given
    email = "test@example.com"
    github_user_id = "abc123"

    django_user_model.objects.create(email=email)

    mock_github_user = mock.MagicMock()
    mocker.patch(
        "custom_auth.oauth.serializers.GithubUser", return_value=mock_github_user
    )
    mock_github_user.get_user_info.return_value = {
        "email": email,
        "first_name": "John",
        "last_name": "Smith",
        "github_user_id": github_user_id,
    }

    url = reverse("api-v1:custom_auth:oauth:github-oauth-login")

    # When
    response = api_client.post(url, data={"access_token": "some-token"})

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert (jwt_access_cookie := response.cookies.get("jwt")) is not None
    assert jwt_access_cookie["httponly"]

    assert not response.data
