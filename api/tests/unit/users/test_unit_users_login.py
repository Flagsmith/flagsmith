from axes.models import AccessAttempt  # type: ignore[import-untyped]
from django.urls import reverse
from pytest_django.fixtures import SettingsWrapper
from rest_framework.test import APIClient


def test_brute_force_access_attempts(
    db: None, settings: SettingsWrapper, api_client: APIClient
) -> None:
    invalid_user_name = "invalid_user@mail.com"
    login_attempts_to_make = settings.AXES_FAILURE_LIMIT + 1

    assert AccessAttempt.objects.all().count() == 0

    login_url = reverse("api-v1:custom_auth:custom-mfa-authtoken-login")
    login_data = {"email": invalid_user_name, "password": "invalid_password"}

    for _ in range(login_attempts_to_make):
        api_client.post(login_url, login_data, format="json")

    assert AccessAttempt.objects.filter(username=invalid_user_name).count() == 1
