import argparse
import logging
from typing import Any

from django.conf import settings
from django.core.management import BaseCommand

from organisations.models import Organisation, OrganisationRole
from users.services import get_initial_superuser

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--email",
            type=str,
            dest="admin_email",
            help="Email address for the superuser",
            default=None,
        )
        parser.add_argument(
            "--organisation-name",
            type=str,
            dest="organisation_name",
            help="Organisation name",
            default=None,
        )

    def handle(
        self,
        *args: Any,
        admin_email: str | None,
        organisation_name: str | None,
        **options: Any,
    ) -> None:
        if not settings.ALLOW_ADMIN_INITIATION_VIA_CLI or Organisation.objects.exists():
            logger.debug("Skipping initial organisation creation.")
            return
        organisation = Organisation.objects.create(
            name=organisation_name or settings.ORGANISATION_NAME
        )
        initial_superuser = get_initial_superuser(admin_email)
        initial_superuser.add_organisation(organisation, OrganisationRole.ADMIN)
        self.stdout.write(
            self.style.SUCCESS(
                'Organisation "%s" created successfully.' % organisation.name
            )
        )
