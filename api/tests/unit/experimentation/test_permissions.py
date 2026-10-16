import pytest
from pytest_django.fixtures import SettingsWrapper
from rest_framework.test import APIRequestFactory

from environments.models import Environment
from experimentation.permissions import ExperimentationPermission
from users.models import FFAdminUser

pytestmark = pytest.mark.django_db


def _check_permission(user: FFAdminUser, environment_api_key: str) -> bool:
    factory = APIRequestFactory()
    request = factory.get("/")
    request.user = user

    class FakeView:
        kwargs = {"environment_api_key": environment_api_key}

    return ExperimentationPermission().has_permission(request, FakeView())  # type: ignore[arg-type]


def test_has_permission__admin__returns_true(
    admin_user: FFAdminUser,
    environment: Environment,
) -> None:
    # Given / When
    result = _check_permission(admin_user, environment.api_key)

    # Then
    assert result is True


def test_has_permission__experimentation_not_deployed__returns_false(
    admin_user: FFAdminUser,
    environment: Environment,
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.EXPERIMENTATION_ENABLED = False

    # When
    result = _check_permission(admin_user, environment.api_key)

    # Then
    assert result is False


def test_has_permission__not_admin__returns_false(
    staff_user: FFAdminUser,
    environment: Environment,
) -> None:
    # Given / When
    result = _check_permission(staff_user, environment.api_key)

    # Then
    assert result is False


def test_has_permission__environment_not_found__returns_false(
    admin_user: FFAdminUser,
) -> None:
    # Given / When
    result = _check_permission(admin_user, "nonexistent-key")

    # Then
    assert result is False
