from unittest.mock import MagicMock

import pytest
from axes.models import AccessAttempt
from django.contrib.auth import authenticate
from django.http import HttpRequest
from pytest_django.fixtures import SettingsWrapper
from rest_framework.exceptions import AuthenticationFailed

from environments.authentication import EnvironmentKeyAuthentication
from environments.models import Environment
from organisations.models import Organisation


def test_authentication_passes_if_valid_api_key_passed(
    environment: Environment,
) -> None:
    # Given
    request = MagicMock()
    request.META.get.return_value = environment.api_key
    authenticator = EnvironmentKeyAuthentication()

    # When / Then - authentication passes
    authenticator.authenticate(request)


def test_authenticate_raises_authentication_failed_if_request_missing_environment_key(
    db: None,
) -> None:
    # Given
    request = MagicMock()
    authenticator = EnvironmentKeyAuthentication()

    # When / Then
    with pytest.raises(AuthenticationFailed):
        authenticator.authenticate(request)


def test_authenticate_raises_authentication_failed_if_request_environment_key_not_found(
    db: None,
) -> None:
    # Given
    request = MagicMock()
    request.META.get.return_value = "some-invalid-key"
    authenticator = EnvironmentKeyAuthentication()

    # When / Then
    with pytest.raises(AuthenticationFailed):
        authenticator.authenticate(request)


def test_authenticate_raises_authentication_failed_if_organisation_set_to_stop_serving_flags(
    organisation: Organisation,
    environment: Environment,
) -> None:
    # Given
    organisation.stop_serving_flags = True
    organisation.save()

    request = MagicMock()
    request.META.get.return_value = environment.api_key
    authenticator = EnvironmentKeyAuthentication()

    # When / Then
    with pytest.raises(AuthenticationFailed):
        authenticator.authenticate(request)


def test_brute_force_access_attempts(db: None, settings: SettingsWrapper) -> None:
    invalid_user_name = "invalid_user"
    login_attempts_to_make = settings.AXES_FAILURE_LIMIT + 1

    assert AccessAttempt.objects.all().count() == 0

    for _ in range(login_attempts_to_make):
        request = HttpRequest()
        authenticate(request, username=invalid_user_name, password="invalid_password")

    assert AccessAttempt.objects.filter(username=invalid_user_name).count() == 1
