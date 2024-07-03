from unittest import mock

from django.test import RequestFactory
from django.utils import timezone
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture
from rest_framework.authtoken.models import Token

from custom_auth.oauth.serializers import (
    GithubLoginSerializer,
    GoogleLoginSerializer,
    OAuthLoginSerializer,
)
from users.models import FFAdminUser, SignUpType


@mock.patch("custom_auth.oauth.serializers.get_user_info")
def test_create_oauth_login_serializer(
    mock_get_user_info: mock.MagicMock, db: None
) -> None:
    # Given
    access_token = "access-token"
    sign_up_type = "NO_INVITE"
    data = {"access_token": access_token, "sign_up_type": sign_up_type}
    rf = RequestFactory()
    request = rf.post("/api/v1/auth/oauth/google/")
    email = "testytester@example.com"
    first_name = "testy"
    last_name = "tester"
    google_user_id = "test-id"

    mock_user_data = {
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "google_user_id": google_user_id,
    }
    serializer = OAuthLoginSerializer(data=data, context={"request": request})

    # monkey patch the get_user_info method to return the mock user data
    serializer.get_user_info = lambda: mock_user_data

    # When
    serializer.is_valid()
    response = serializer.save()

    # Then
    assert FFAdminUser.objects.filter(email=email, sign_up_type=sign_up_type).exists()
    assert isinstance(response, Token)
    assert (timezone.now() - response.user.last_login).seconds < 5
    assert response.user.email == email


@mock.patch("custom_auth.oauth.serializers.get_user_info")
def test_get_user_info_with_google_login(
    mock_get_user_info: mock.MagicMock,
) -> None:
    # Given
    rf = RequestFactory()
    request = rf.post("placeholer-login-url")
    access_token = "some-access-token"
    serializer = GoogleLoginSerializer(
        data={"access_token": access_token}, context={"request": request}
    )

    # When
    serializer.is_valid()
    serializer.get_user_info()

    # Then
    mock_get_user_info.assert_called_with(access_token)


@mock.patch("custom_auth.oauth.serializers.GithubUser")
def test_get_user_info_with_github_login(
    mock_github_user_serializer: mock.MagicMock,
) -> None:
    # Given
    rf = RequestFactory()
    request = rf.post("placeholer-login-url")
    access_token = "some-access-token"
    serializer = GithubLoginSerializer(
        data={"access_token": access_token}, context={"request": request}
    )

    mock_github_user = mock.MagicMock()
    mock_github_user_serializer.return_value = mock_github_user

    # When
    serializer.is_valid()
    serializer.get_user_info()

    # Then
    mock_github_user_serializer.assert_called_with(code=access_token)
    mock_github_user.get_user_info.assert_called()


def test_OAuthLoginSerializer_calls_is_authentication_method_valid_correctly_if_auth_controller_is_installed(
    settings, rf, mocker, db
):
    # Given
    settings.AUTH_CONTROLLER_INSTALLED = True

    request = rf.post("/some-login/url")
    user_email = "test_user@test.com"
    mocked_auth_controller = mocker.MagicMock()
    mocker.patch.dict(
        "sys.modules", {"auth_controller.controller": mocked_auth_controller}
    )

    serializer = OAuthLoginSerializer(
        data={"access_token": "some_token"}, context={"request": request}
    )
    # monkey patch the get_user_info method to return the mock user data
    serializer.get_user_info = lambda: {"email": user_email}

    serializer.is_valid(raise_exception=True)

    # When
    serializer.save()

    # Then
    mocked_auth_controller.is_authentication_method_valid.assert_called_with(
        request,
        email=user_email,
        raise_exception=True,
    )


def test_OAuthLoginSerializer_allows_registration_if_sign_up_type_is_invite_link(
    settings: SettingsWrapper, rf: RequestFactory, mocker: MockerFixture, db: None
):
    # Given
    settings.ALLOW_REGISTRATION_WITHOUT_INVITE = False

    request = rf.post("/api/v1/auth/users/")
    user_email = "test_user@test.com"

    serializer = OAuthLoginSerializer(
        data={
            "access_token": "some_token",
            "sign_up_type": SignUpType.INVITE_LINK.value,
        },
        context={"request": request},
    )
    # monkey patch the get_user_info method to return the mock user data
    serializer.get_user_info = lambda: {"email": user_email}

    serializer.is_valid(raise_exception=True)

    # When
    user = serializer.save()

    # Then
    assert user
