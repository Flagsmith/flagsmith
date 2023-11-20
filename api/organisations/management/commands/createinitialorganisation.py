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
            default=settings.ADMIN_EMAIL,
        )
        parser.add_argument(
            "--organisation-name",
            type=str,
            dest="organisation_name",
            help="Organisation name",
            default=settings.ORGANISATION_NAME,
        )

    def handle(
        self,
        *args: Any,
        admin_email: str,
        organisation_name: str,
        **options: Any,
    ) -> None:
        if not settings.ALLOW_ADMIN_INITIATION_VIA_CLI or Organisation.objects.exists():
            logger.debug("Skipping initial organisation creation.")
            return
        organisation = Organisation.objects.create(name=organisation_name)
        initial_superuser = get_initial_superuser(admin_email)
        initial_superuser.add_organisation(organisation, OrganisationRole.ADMIN)
        self.stdout.write(
            self.style.SUCCESS(
                'Organisation "%s" created successfully.' % organisation.name
            )
        )
