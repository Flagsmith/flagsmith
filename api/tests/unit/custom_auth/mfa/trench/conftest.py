import pytest

from custom_auth.mfa.trench.models import MFAMethod
from users.models import FFAdminUser


@pytest.fixture()
def mfa_app_method(admin_user: FFAdminUser):
    return MFAMethod.objects.create(
        user=admin_user, name="app", secret="secret", is_active=True, is_primary=True
    )
