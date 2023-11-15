from django.conf import settings

from users.models import FFAdminUser


def is_initial_config_allowed() -> bool:
    return not FFAdminUser.objects.count()


def create_initial_superuser(
    admin_email: str | None = None,
    admin_initial_password: str | None = None,
) -> FFAdminUser:
    return FFAdminUser.objects.create_superuser(
        email=admin_email or settings.ADMIN_EMAIL,
        password=admin_initial_password or settings.ADMIN_INITIAL_PASSWORD,
        is_active=True,
    )
