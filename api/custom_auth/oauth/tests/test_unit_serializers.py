from unittest import TestCase, mock

import pytest
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.utils import timezone
from rest_framework.authtoken.models import Token

from custom_auth.oauth.serializers import (
    GithubLoginSerializer,
    GoogleLoginSerializer,
    OAuthLoginSerializer,
)

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
        self.request = rf.post("test-login-url")

    @mock.patch("custom_auth.oauth.serializers.get_user_info")
    def test_create(self, mock_get_user_info):
        # Given
        access_token = "access-token"
        data = {"access_token": access_token}
        serializer = OAuthLoginSerializer(data=data, context={"request": self.request})

        # monkey patch the get_user_info method to return the mock user data
        serializer.get_user_info = lambda: self.mock_user_data

        # When
        serializer.is_valid()
        response = serializer.save()

        # Then
        assert UserModel.objects.filter(email=self.test_email).exists()
        assert isinstance(response, Token)
        assert (timezone.now() - response.user.last_login).seconds < 5
        assert response.user.email == self.test_email


class GoogleLoginSerializerTestCase(TestCase):
    def setUp(self) -> None:
        rf = RequestFactory()
        self.request = rf.post("test-login-url")

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
        self.request = rf.post("test-login-url")

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
