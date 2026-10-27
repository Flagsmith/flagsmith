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


def test_createadminuser__existing_regular_user__raises_error(
    staff_user: FFAdminUser,
) -> None:
    # Given / When
    with pytest.raises(CommandError):
        call_command("createadminuser", "--email", staff_user.email, "--enforce-sso")

    # Then
    staff_user.refresh_from_db()
    assert not staff_user.is_superuser
    assert not Assignment.objects.exists()
