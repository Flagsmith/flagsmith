import argparse
from typing import Any

from admin_sso.default_settings import ASSIGNMENT_MATCH
from admin_sso.models import Assignment
from django.conf import settings
from django.core.management import BaseCommand, CommandError

from users.services import create_superuser, should_skip_create_initial_superuser


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
        if (
            not should_skip_create_initial_superuser()
            and not settings.ALLOW_ADMIN_INITIATION_VIA_CLI
        ):
            raise CommandError(
                "There are no superusers yet. Set `ALLOW_ADMIN_INITIATION_VIA_CLI`"
            )

        superuser = create_superuser(admin_email=email).user
        if enforce_sso:
            username, domain = email.split("@")
            Assignment.objects.get_or_create(
                username_mode=ASSIGNMENT_MATCH,
                username=username,
                domain=domain,
                user=superuser,
            )

        self.stdout.write(
            self.style.SUCCESS('Superuser "%s" created successfully.' % superuser.email)
        )
