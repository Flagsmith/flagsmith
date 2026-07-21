from unittest.mock import MagicMock

import pytest
from rest_framework.exceptions import AuthenticationFailed

from environments.authentication import EnvironmentKeyAuthentication
from environments.models import Environment
from organisations.models import Organisation


def test_environment_key_authentication__valid_api_key__passes(
    environment: Environment,
) -> None:
    # Given
    request = MagicMock()
    request.META.get.return_value = environment.api_key
    authenticator = EnvironmentKeyAuthentication()

    # When / Then - authentication passes
    authenticator.authenticate(request)  # type: ignore[no-untyped-call]


def test_environment_key_authentication__missing_environment_key__raises_authentication_failed(
    db: None,
) -> None:
    # Given
    request = MagicMock()
    authenticator = EnvironmentKeyAuthentication()

    # When / Then
    with pytest.raises(AuthenticationFailed):
        authenticator.authenticate(request)  # type: ignore[no-untyped-call]


def test_environment_key_authentication__environment_key_not_found__raises_authentication_failed(
    db: None,
) -> None:
    # Given
    request = MagicMock()
    request.META.get.return_value = "some-invalid-key"
    authenticator = EnvironmentKeyAuthentication()

    # When / Then
    with pytest.raises(AuthenticationFailed):
        authenticator.authenticate(request)  # type: ignore[no-untyped-call]


def test_environment_key_authentication__organisation_stop_serving_flags__raises_authentication_failed(
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
        authenticator.authenticate(request)  # type: ignore[no-untyped-call]
