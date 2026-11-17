from dataclasses import dataclass

from admin_sso.default_settings import ASSIGNMENT_MATCH
from admin_sso.models import Assignment
from django.conf import settings
from djoser.email import PasswordResetEmail  # type: ignore[import-untyped]

from core.helpers import get_current_site_url
from users.models import FFAdminUser


@dataclass
class CreateSuperuserResponse:
    user: FFAdminUser
    password_reset_url: str


def should_skip_create_initial_superuser() -> bool:
    return FFAdminUser.objects.exists()


def create_superuser(
    admin_email: str | None = None,
    enforce_sso: bool = False,
) -> CreateSuperuserResponse:
    """Create or promote a superuser"""
    email = (admin_email or settings.ADMIN_EMAIL).lower()
    superuser = FFAdminUser.objects.filter(email__iexact=email).first()

    if superuser:
        superuser.is_staff = superuser.is_superuser = True
        superuser.save(update_fields=["is_staff", "is_superuser"])
    else:
        superuser = FFAdminUser.objects.create_superuser(  # type: ignore[no-untyped-call]
            email=email,
            is_active=True,
            password=None,
        )

    if enforce_sso:
        username, domain = email.split("@")
        Assignment.objects.get_or_create(
            username_mode=ASSIGNMENT_MATCH,
            username=username,
            domain=domain,
            user=superuser,
        )

    return CreateSuperuserResponse(
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
    return f"{get_current_site_url()}/{_email.get_context_data()['url']}"
