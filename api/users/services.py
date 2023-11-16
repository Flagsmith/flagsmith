from django.conf import settings

from users.models import FFAdminUser


def should_skip_create_initial_superuser() -> bool:
    return FFAdminUser.objects.exists()


def create_initial_superuser(
    admin_email: str | None = None,
    admin_initial_password: str | None = None,
) -> FFAdminUser:
    return FFAdminUser.objects.create_superuser(
        email=admin_email or settings.ADMIN_EMAIL,
        password=admin_initial_password or settings.ADMIN_INITIAL_PASSWORD,
        is_active=True,
    )


def get_initial_superuser(
    admin_email: str | None = None,
) -> FFAdminUser | None:
    return FFAdminUser.objects.filter(email=admin_email or settings.ADMIN_EMAIL).first()
