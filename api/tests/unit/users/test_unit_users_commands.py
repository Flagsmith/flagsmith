import pytest
from admin_sso.models import Assignment
from django.core.management import CommandError, call_command
from pytest_django.fixtures import SettingsWrapper

from users.models import FFAdminUser

pytestmark = pytest.mark.django_db


def test_createadminuser__new_email__creates_superuser_without_password(
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.ALLOW_ADMIN_INITIATION_VIA_CLI = True

    # When
    call_command("createadminuser", "--email", "admin@example.com")

    # Then
    superuser = FFAdminUser.objects.get(email="admin@example.com")
    assert superuser.is_superuser
    assert not superuser.has_usable_password()
    assert not Assignment.objects.exists()


def test_createadminuser__enforce_sso_run_twice__creates_one_sso_superuser(
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.ALLOW_ADMIN_INITIATION_VIA_CLI = True

    # When
    call_command("createadminuser", "--email", "admin@example.com", "--enforce-sso")
    call_command("createadminuser", "--email", "admin@example.com", "--enforce-sso")

    # Then
    superuser = FFAdminUser.objects.get()
    assert Assignment.objects.get() == Assignment.objects.for_email(superuser.email)
    assert Assignment.objects.get().user == superuser


def test_createadminuser__existing_regular_user__promotes_to_superuser(
    settings: SettingsWrapper,
    staff_user: FFAdminUser,
) -> None:
    # Given
    settings.ALLOW_ADMIN_INITIATION_VIA_CLI = True

    # When
    call_command(
        "createadminuser", "--email", staff_user.email.upper(), "--enforce-sso"
    )

    # Then
    staff_user.refresh_from_db()
    assert staff_user.is_superuser
    assert staff_user.is_staff
    assert Assignment.objects.get().user == staff_user


def test_createinitialadminuser__users_exist_and_force__creates_superuser(
    settings: SettingsWrapper,
    staff_user: FFAdminUser,
) -> None:
    # Given
    settings.ALLOW_ADMIN_INITIATION_VIA_CLI = True

    # When
    call_command("createinitialadminuser", "--email", "admin@example.com", "--force")

    # Then
    assert FFAdminUser.objects.get(email="admin@example.com").is_superuser


def test_createadminuser__no_superuser_and_cli_initiation_disallowed__raises_error() -> (
    None
):
    # Given / When
    with pytest.raises(CommandError):
        call_command("createadminuser", "--email", "admin@example.com")

    # Then
    assert not FFAdminUser.objects.exists()
