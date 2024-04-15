from unittest import TestCase, mock

import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory, override_settings
from django.utils import timezone
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed

from audit.models import AuditLog, RelatedObjectType
from custom_auth.oauth.serializers import (
    GithubLoginSerializer,
    GoogleLoginSerializer,
    OAuthLoginSerializer,
)
from organisations.models import Organisation
from users.models import SignUpType

UserModel = get_user_model()


@pytest.mark.django_db
class OAuthLoginSerializerTestCase(TestCase):
    def setUp(self) -> None:
        self.test_email = "testytester@example.com"
        self.test_first_name = "testy"
        self.test_last_name = "tester"
        self.test_id = "test-id"
        self.mock_user_data = {
            "email": self.test_email,
            "first_name": self.test_first_name,
            "last_name": self.test_last_name,
            "google_user_id": self.test_id,
        }
        rf = RequestFactory()
        self.request = rf.post("placeholder-login-url")

    @mock.patch("django.contrib.auth.models.timezone", autospec=True)
    def test_create(self, mock_timezone):
        # Given
        now = timezone.now()
        mock_timezone.now.return_value = now

        access_token = "access-token"
        sign_up_type = "NO_INVITE"
        data = {"access_token": access_token, "sign_up_type": sign_up_type}
        serializer = OAuthLoginSerializer(data=data, context={"request": self.request})

        # monkey patch the get_user_info method to return the mock user data
        serializer.get_user_info = lambda: self.mock_user_data

        # When
        serializer.is_valid()
        token = serializer.save()

        # Then
        assert UserModel.objects.filter(
            email=self.test_email, sign_up_type=sign_up_type
        ).exists()
        assert isinstance(token, Token)
        assert token.user.email == self.test_email
        assert token.user.first_name == self.test_first_name
        assert token.user.last_name == self.test_last_name
        assert token.user.google_user_id == self.test_id
        assert token.user.last_login == now

    @mock.patch("django.contrib.auth.models.timezone", autospec=True)
    def test_save_existing(self, mock_timezone):
        # Given
        now = timezone.now()
        mock_timezone.now.return_value = now

        access_token = "access-token"
        sign_up_type = "NO_INVITE"
        data = {"access_token": access_token, "sign_up_type": sign_up_type}
        serializer = OAuthLoginSerializer(data=data, context={"request": self.request})

        # make existing user/organisation to audit log against
        organisation = Organisation.objects.create(name="Test Org")
        user = UserModel.objects.create(
            **self.mock_user_data, sign_up_type=sign_up_type
        )
        user.organisations.add(organisation)

        # monkey patch the get_user_info method to return the mock user data
        serializer.get_user_info = lambda: self.mock_user_data

        # When
        serializer.is_valid()
        token = serializer.save()

        # Then
        assert UserModel.objects.filter(
            email=self.test_email, sign_up_type=sign_up_type
        ).exists()
        assert isinstance(token, Token)
        assert token.user.email == self.test_email
        assert token.user.first_name == self.test_first_name
        assert token.user.last_name == self.test_last_name
        assert token.user.google_user_id == self.test_id
        assert token.user.last_login == now

        # and
        assert (
            AuditLog.objects.filter(
                related_object_type=RelatedObjectType.USER.name
            ).count()
            == 1
        )
        audit_log = AuditLog.objects.first()
        assert audit_log
        assert audit_log.author_id == user.pk
        assert audit_log.related_object_type == RelatedObjectType.USER.name
        assert audit_log.related_object_id == user.pk
        assert audit_log.organisation_id == organisation.pk
        assert audit_log.log == f"User logged in: {self.test_email}"

    @override_settings(AUTH_CONTROLLER_INSTALLED=True)
    @mock.patch("django.contrib.auth.models.timezone", autospec=True)
    def test_save_denied(self, mock_timezone):
        # Given
        access_token = "access-token"
        sign_up_type = "NO_INVITE"
        data = {"access_token": access_token, "sign_up_type": sign_up_type}
        serializer = OAuthLoginSerializer(data=data, context={"request": self.request})

        # make existing user/organisation to audit log against
        organisation = Organisation.objects.create(name="Test Org")
        user = UserModel.objects.create(
            **self.mock_user_data, sign_up_type=sign_up_type
        )
        user.organisations.add(organisation)

        # monkey patch the get_user_info method to return the mock user data
        serializer.get_user_info = lambda: self.mock_user_data

        # monkey patch is_authentication_method_valid to raise AuthenticationFailed
        mocked_auth_controller = mock.MagicMock()
        mocked_auth_controller.is_authentication_method_valid.side_effect = (
            AuthenticationFailed("Authentication controlled", code="invalid_auth_test")
        )

        # When
        with mock.patch.dict(
            "sys.modules", {"auth_controller.controller": mocked_auth_controller}
        ):
            serializer.is_valid()
            with pytest.raises(AuthenticationFailed):
                serializer.save()

        # Then
        assert (
            AuditLog.objects.filter(
                related_object_type=RelatedObjectType.USER.name
            ).count()
            == 1
        )
        audit_log = AuditLog.objects.first()
        assert audit_log
        assert audit_log.author_id == user.pk
        assert audit_log.related_object_type == RelatedObjectType.USER.name
        assert audit_log.related_object_id == user.pk
        assert audit_log.organisation_id == organisation.pk
        assert (
            audit_log.log == f"User login failed (invalid_auth_test): {self.test_email}"
        )


class GoogleLoginSerializerTestCase(TestCase):
    def setUp(self) -> None:
        rf = RequestFactory()
        self.request = rf.post("placeholder-login-url")

    @mock.patch("custom_auth.oauth.serializers.get_user_info")
    def test_get_user_info(self, mock_get_user_info):
        # Given
        access_token = "some-access-token"
        serializer = GoogleLoginSerializer(
            data={"access_token": access_token}, context={"request": self.request}
        )

        # When
        serializer.is_valid()
        serializer.get_user_info()

        # Then
        mock_get_user_info.assert_called_with(access_token)


class GithubLoginSerializerTestCase(TestCase):
    def setUp(self) -> None:
        rf = RequestFactory()
        self.request = rf.post("placeholder-login-url")

    @mock.patch("custom_auth.oauth.serializers.GithubUser")
    def test_get_user_info(self, MockGithubUser):
        # Given
        access_token = "some-access-token"
        serializer = GithubLoginSerializer(
            data={"access_token": access_token}, context={"request": self.request}
        )

        mock_github_user = mock.MagicMock()
        MockGithubUser.return_value = mock_github_user

        # When
        serializer.is_valid()
        serializer.get_user_info()

        # Then
        MockGithubUser.assert_called_with(code=access_token)
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
    token = serializer.save()

    # Then
    assert UserModel.objects.filter(
        email=user_email, sign_up_type=SignUpType.INVITE_LINK
    ).exists()
    assert isinstance(token, Token)
    assert token.user.email == user_email
