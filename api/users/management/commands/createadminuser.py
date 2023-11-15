import argparse
import sys
from typing import Any

from django.core.management import BaseCommand, CommandError

from users.services import create_initial_superuser, is_initial_config_allowed


class Command(BaseCommand):
    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--password-stdin",
            dest="password_stdin",
            action="store_true",
            default=False,
            help="Initial password for the superuser. Provide the password through STDIN",
        )
        parser.add_argument(
            "--email",
            type=str,
            dest="admin_email",
            help="Email address for the superuser",
            default=None,
        )

    def handle(
        self,
        *args: Any,
        admin_email: str | None,
        password_stdin: bool,
        **options: Any,
    ) -> None:
        if not is_initial_config_allowed():
            raise CommandError("Flagsmith admin user already configured")
        admin_initial_password = sys.stdin.read().strip() if password_stdin else None
        create_initial_superuser(
            admin_email=admin_email,
            admin_initial_password=admin_initial_password,
        )
        self.stdout.write(
            self.style.SUCCESS('Superuser "%s" created successfully.' % admin_email)
        )
