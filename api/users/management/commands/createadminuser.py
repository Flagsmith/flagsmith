import argparse
from typing import Any

from admin_sso.default_settings import ASSIGNMENT_MATCH
from admin_sso.models import Assignment
from django.core.management import BaseCommand, CommandError

from users.models import FFAdminUser


class Command(BaseCommand):
    help = "Create a superuser, unless it exists already"

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--email",
            type=str,
            required=True,
            help="Email address for the superuser",
        )
        parser.add_argument(
            "--enforce-sso",
            action="store_true",
            help="Allow the superuser to log in to Django admin through SSO",
        )

    def handle(
        self,
        *args: Any,
        email: str,
        enforce_sso: bool,
        **options: Any,
    ) -> None:
        superuser = self._get_or_create_superuser(email)
        if enforce_sso:
            username, domain = superuser.email.split("@")
            Assignment.objects.get_or_create(
                username_mode=ASSIGNMENT_MATCH,
                username=username,
                domain=domain,
                user=superuser,
            )

    def _get_or_create_superuser(self, email: str) -> FFAdminUser:
        user: FFAdminUser | None = FFAdminUser.objects.filter(
            email__iexact=email
        ).first()
        if user is None:
            user = FFAdminUser.objects.create_superuser(  # type: ignore[no-untyped-call]
                email=email, password=None, is_active=True
            )
            self.stdout.write(
                self.style.SUCCESS(f'Superuser "{email}" created successfully.')
            )
        if not user.is_superuser:
            raise CommandError(f'User "{email}" exists and is not a superuser.')
        return user
