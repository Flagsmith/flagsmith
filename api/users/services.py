from dataclasses import dataclass

from core.helpers import get_current_site_url
from django.conf import settings
from djoser.email import PasswordResetEmail

from users.models import FFAdminUser


@dataclass
class CreateInitialSuperuserResponse:
    user: FFAdminUser
    password_reset_url: str


def should_skip_create_initial_superuser() -> bool:
    return FFAdminUser.objects.exists()


def create_initial_superuser(
    admin_email: str | None = None,
) -> CreateInitialSuperuserResponse:
    superuser = FFAdminUser.objects.create_superuser(
        email=admin_email or settings.ADMIN_EMAIL,
        is_active=True,
        password=None,
    )
    return CreateInitialSuperuserResponse(
        user=superuser,
        password_reset_url=_get_user_password_reset_url(superuser),
    )


def get_initial_superuser(
    admin_email: str | None = None,
) -> FFAdminUser | None:
    return FFAdminUser.objects.filter(email=admin_email or settings.ADMIN_EMAIL).first()


def _get_user_password_reset_url(
    user: FFAdminUser,
) -> str:
    _email = PasswordResetEmail(context={"user": user})
    return f'{get_current_site_url()}/{_email.get_context_data()["url"]}'
