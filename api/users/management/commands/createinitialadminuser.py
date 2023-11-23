import argparse
import logging
from typing import Any

from django.conf import settings
from django.core.management import BaseCommand

from users.services import (
    create_initial_superuser,
    should_skip_create_initial_superuser,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--email",
            type=str,
            dest="admin_email",
            help="Email address for the superuser",
            default=settings.ADMIN_EMAIL,
        )

    def handle(
        self,
        *args: Any,
        admin_email: str,
        **options: Any,
    ) -> None:
        if (
            not settings.ALLOW_ADMIN_INITIATION_VIA_CLI
            or should_skip_create_initial_superuser()
        ):
            logger.debug("Skipping initial user creation.")
            return
        response = create_initial_superuser(
            admin_email=admin_email,
        )
        self.stdout.write(
            self.style.SUCCESS(
                'Superuser "%s" created successfully.' % response.user.email
            )
        )
        self.stdout.write(
            self.style.SUCCESS(
                "Please go to the following page and choose a password: %s"
                % response.password_reset_url
            )
        )
