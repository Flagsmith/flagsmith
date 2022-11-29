import os

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from users.models import FFAdminUser


def test_e2e_teardown(settings, db):
    # TODO: tidy up this hack to fix throttle rates
    settings.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["signup"] = "1000/min"
    token = "test-token"
    e2e_user_email = "test@example.com"
    register_url = "/api/v1/auth/users/"

    os.environ["E2E_TEST_AUTH_TOKEN"] = token
    os.environ["FE_E2E_TEST_USER_EMAIL"] = e2e_user_email

    client = APIClient(HTTP_X_E2E_TEST_AUTH_TOKEN=token)

    # Register a user with the e2e test user email address
    test_password = FFAdminUser.objects.make_random_password()
    register_data = {
        "email": os.environ["FE_E2E_TEST_USER_EMAIL"],
        "first_name": "test",
        "last_name": "test",
        "password": test_password,
        "re_password": test_password,
    }
    register_response = client.post(register_url, data=register_data)
    assert register_response.status_code == status.HTTP_201_CREATED

    # then test that we can teardown that user
    url = reverse("api-v1:e2etests:teardown")
    teardown_response = client.post(url)
    assert teardown_response.status_code == status.HTTP_204_NO_CONTENT
    assert not FFAdminUser.objects.filter(email=e2e_user_email).exists()
