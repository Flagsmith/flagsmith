import pytest

from custom_auth.mfa.trench.command.create_secret import create_secret_command
from custom_auth.mfa.trench.command.replace_mfa_method_backup_codes import (
    regenerate_backup_codes_for_mfa_method_command,
)
from custom_auth.mfa.trench.models import MFAMethod
from users.models import FFAdminUser


@pytest.fixture()
def mfa_app_method(admin_user: FFAdminUser) -> MFAMethod:
    mfa = MFAMethod.objects.create(
        user=admin_user,
        name="app",
        secret=create_secret_command(),
        is_active=True,
        is_primary=True,
    )
    # Generate backup codes
    regenerate_backup_codes_for_mfa_method_command(admin_user.id, mfa.name)
    return mfa


@pytest.fixture()
def deactivated_mfa_app_method(mfa_app_method: MFAMethod) -> MFAMethod:
    mfa_app_method.is_active = False
    mfa_app_method.is_primary = False
    mfa_app_method.save()
    return mfa_app_method
