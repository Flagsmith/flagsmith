from unittest import TestCase, mock

import pytest
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

from custom_auth.oauth.serializers import OAuthAccessTokenSerializer

UserModel = get_user_model()


@pytest.mark.django_db
class OAuthAccessTokenSerializerTestCase(TestCase):
    def setUp(self) -> None:
        self.test_email = "testytester@example.com"
        self.test_first_name = "testy"
        self.test_last_name = "tester"
        self.test_id = "test-id"
        self.mock_user_data = {
            "email": self.test_email,
            "first_name": self.test_first_name,
            "last_name": self.test_last_name,
            "google_user_id": self.test_id
        }

    @mock.patch("custom_auth.oauth.serializers.get_user_info")
    def test_create(self, mock_get_user_info):
        # Given
        access_token = "access-token"
        serializer = OAuthAccessTokenSerializer()
        data = {
            "access_token": access_token
        }

        mock_get_user_info.return_value = self.mock_user_data

        # When
        response = serializer.create(validated_data=data)

        # Then
        assert UserModel.objects.filter(email=self.test_email).exists()
        assert isinstance(response, Token)
        assert response.user.email == self.test_email
