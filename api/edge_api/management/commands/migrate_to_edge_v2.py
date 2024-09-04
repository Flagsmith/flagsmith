import logging
from typing import Any

from django.core.management import BaseCommand

from projects.models import EdgeV2MigrationStatus, Project
from projects.tasks import migrate_project_environments_to_v2

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args: Any, **options: Any) -> str | None:
        for project_id in Project.objects.filter(
            edge_v2_migration_status__in=(
                EdgeV2MigrationStatus.NOT_STARTED,
                EdgeV2MigrationStatus.INCOMPLETE,
            )
        ).values_list("id", flat=True):
            try:
                migrate_project_environments_to_v2(project_id)
            except Exception:  # pragma: no cover
                logger.exception("Error migrating project id=%d", project_id)
