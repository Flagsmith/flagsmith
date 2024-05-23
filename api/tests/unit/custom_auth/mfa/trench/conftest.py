import pytest

from custom_auth.mfa.trench.command.create_secret import create_secret_command
from custom_auth.mfa.trench.models import MFAMethod
from users.models import FFAdminUser


@pytest.fixture()
def mfa_app_method(admin_user: FFAdminUser):
    return MFAMethod.objects.create(
        user=admin_user,
        name="app",
        secret=create_secret_command(),
        is_active=True,
        is_primary=True,
    )
