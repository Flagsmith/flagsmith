import os
from unittest import TestCase

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from users.models import FFAdminUser


@pytest.mark.django_db
class E2eTestsIntegrationTestCase(TestCase):
    register_url = "/api/v1/auth/users/"

    def setUp(self) -> None:
        token = "test-token"
        self.e2e_user_email = "test@example.com"
        os.environ["E2E_TEST_AUTH_TOKEN"] = token
        os.environ["FE_E2E_TEST_USER_EMAIL"] = self.e2e_user_email
        self.client = APIClient(HTTP_X_E2E_TEST_AUTH_TOKEN=token)

    def test_e2e_teardown(self):
        # Register a user with the e2e test user email address
        test_password = FFAdminUser.objects.make_random_password()
        register_data = {
            "email": self.e2e_user_email,
            "first_name": "test",
            "last_name": "test",
            "password": test_password,
            "re_password": test_password
        }
        register_response = self.client.post(self.register_url, data=register_data)
        assert register_response.status_code == status.HTTP_201_CREATED

        # then test that we can teardown that user
        url = reverse("api-v1:e2etests:teardown")
        teardown_response = self.client.post(url)
        assert teardown_response.status_code == status.HTTP_204_NO_CONTENT
        assert not FFAdminUser.objects.filter(email=self.e2e_user_email).exists()
