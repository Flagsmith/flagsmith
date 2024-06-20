from unittest import mock

from django.db.models import Model
from django.test import override_settings
from django.urls import reverse
from pytest_mock import MockerFixture
from rest_framework import status
from rest_framework.test import APIClient

from organisations.invites.models import Invite
from organisations.models import Organisation


@mock.patch("custom_auth.oauth.serializers.get_user_info")
@override_settings(ALLOW_REGISTRATION_WITHOUT_INVITE=False)
def test_cannot_register_with_google_without_invite_if_registration_disabled(
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
def test_cannot_register_with_github_without_invite_if_registration_disabled(
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
def test_can_register_with_google_with_invite_if_registration_disabled(
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
    response = client.post(url, data={"access_token": "some-token"})

    # Then
    assert response.status_code == status.HTTP_200_OK


@mock.patch("custom_auth.oauth.serializers.GithubUser")
@override_settings(ALLOW_REGISTRATION_WITHOUT_INVITE=False)
def test_can_register_with_github_with_invite_if_registration_disabled(
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
    response = client.post(url, data={"access_token": "some-token"})

    # Then
    assert response.status_code == status.HTTP_200_OK


@mock.patch("custom_auth.oauth.serializers.get_user_info")
@override_settings(ALLOW_OAUTH_REGISTRATION_WITHOUT_INVITE=False)
def test_can_login_with_google_if_registration_disabled(
    mock_get_user_info, db, django_user_model
):
    # Given
    url = reverse("api-v1:custom_auth:oauth:google-oauth-login")
    client = APIClient()

    email = "test@example.com"
    mock_get_user_info.return_value = {"email": email}
    django_user_model.objects.create(email=email)

    # When
    response = client.post(url, data={"access_token": "some-token"})

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert "key" in response.json()


@mock.patch("custom_auth.oauth.serializers.GithubUser")
@override_settings(ALLOW_OAUTH_REGISTRATION_WITHOUT_INVITE=False)
def test_can_login_with_github_if_registration_disabled(
    MockGithubUser, db, django_user_model
):
    # Given
    url = reverse("api-v1:custom_auth:oauth:github-oauth-login")
    client = APIClient()

    email = "test@example.com"
    mock_github_user = mock.MagicMock()
    MockGithubUser.return_value = mock_github_user
    mock_github_user.get_user_info.return_value = {"email": email}
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

    django_user_model.objects.create(email=email_lower)

    mocker.patch("custom_auth.oauth.serializers.get_user_info", return_value={
        "email": email_upper,
        "first_name": "John",
        "last_name": "Smith",
        "google_user_id": google_user_id
    })

    url = reverse("api-v1:custom_auth:oauth:google-oauth-login")

    # When
    response = api_client.post(url, data={"access_token": "some-token"})

    # Then
    assert response.status_code == status.HTTP_200_OK

    qs = django_user_model.objects.filter(email__iexact=email_lower)
    assert qs.count() == 1

    user = qs.first()
    assert user.email == email_lower
    assert user.google_user_id == google_user_id
