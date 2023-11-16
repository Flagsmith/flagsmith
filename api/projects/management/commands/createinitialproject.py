import argparse
import logging
from typing import Any

from django.conf import settings
from django.core.management import BaseCommand

from organisations.models import Organisation
from projects.models import Project

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument(
            "--organisation-name",
            type=str,
            dest="organisation_name",
            help="Project name",
            default=None,
        )
        parser.add_argument(
            "--project-name",
            type=str,
            dest="project_name",
            help="Project name",
            default=None,
        )

    def handle(
        self,
        *args: Any,
        organisation_name: str | None,
        project_name: str | None,
        **options: Any,
    ) -> None:
        organisation = Organisation.objects.filter(
            name=organisation_name or settings.ORGANISATION_NAME
        ).first()
        if (
            not settings.ALLOW_ADMIN_INITIATION_VIA_CLI
            or not organisation
            or Project.objects.count()
        ):
            logger.debug("Skipping initial project creation.")
            return
        project = Project.objects.create(
            name=project_name or settings.PROJECT_NAME,
            organisation=organisation,
        )
        self.stdout.write(
            self.style.SUCCESS('Project "%s" created successfully.' % project.name)
        )
