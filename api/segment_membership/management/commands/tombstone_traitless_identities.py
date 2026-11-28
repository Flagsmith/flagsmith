from argparse import ArgumentParser
from typing import Any

import structlog
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db.models import QuerySet

from environments.models import Environment
from organisations.models import Organisation
from projects.models import Project
from segment_membership.models import SegmentMembershipSeed
from segment_membership.services import (
    enqueue_membership_refresh,
    open_clickhouse_cursor,
)

logger = structlog.get_logger("segment_membership")

# Bug #8499: Query to size traitless ClickHouse identities left behind by earlier seeds.
_SIZING_SQL = """
SELECT count() AS traitless
FROM IDENTITIES FINAL
WHERE environment_id = %(env_key)s
  AND is_deleted = false
  AND empty(JSONAllPaths(traits))
"""

# Bug #8499: Query to insert tombstones superseding traitless rows with inserted_at + 1s.
_TOMBSTONE_SQL = """
INSERT INTO IDENTITIES
    (environment_id, identifier, identity_key, traits, inserted_at, source, is_deleted)
SELECT environment_id, identifier, identity_key, traits,
       inserted_at + INTERVAL 1 SECOND, 'cleanup', true
FROM IDENTITIES FINAL
WHERE environment_id = %(env_key)s
  AND is_deleted = false
  AND empty(JSONAllPaths(traits))
"""


class Command(BaseCommand):
    help = (
        "Tombstone traitless ClickHouse identities left behind by earlier seeding runs."
    )

    def add_arguments(self, parser: ArgumentParser) -> None:
        group = parser.add_mutually_exclusive_group()
        group.add_argument(
            "--organisation-id",
            type=int,
            default=None,
            help="Limit tombstoning to a specific organisation ID.",
        )
        group.add_argument(
            "--environment-id",
            type=int,
            default=None,
            help="Limit tombstoning to a specific environment ID.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Report candidate traitless identities without executing inserts or recounts.",
        )
        parser.add_argument(
            "--skip-recount",
            action="store_true",
            default=False,
            help="Skip scheduling segment membership count refreshes.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        if not settings.CLICKHOUSE_ENABLED:
            self.stdout.write(
                self.style.WARNING("ClickHouse is not enabled. Skipping.")
            )
            return

        dry_run: bool = options["dry_run"]
        skip_recount: bool = options["skip_recount"]
        organisation_id: int | None = options["organisation_id"]
        environment_id: int | None = options["environment_id"]

        environments = self._resolve_environments(organisation_id, environment_id)

        scanned_environments = 0
        tombstoned_total = 0
        modified_projects: set[Project] = set()
        failed_environments: list[int] = []

        for environment in environments.iterator():
            scanned_environments += 1
            env_key = environment.api_key
            log_comment = (
                f"flagsmith:segment_membership:tombstone:"
                f"org_{environment.project.organisation_id}:env_{environment.id}"
            )
            try:
                tombstoned_count = self._process_environment(
                    environment=environment,
                    env_key=env_key,
                    log_comment=log_comment,
                    dry_run=dry_run,
                )
                tombstoned_total += tombstoned_count
                if tombstoned_count > 0 and not dry_run:
                    modified_projects.add(environment.project)
            except Exception as e:
                failed_environments.append(environment.id)
                logger.exception(
                    "tombstone.environment.failed",
                    environment__id=environment.id,
                    project__id=environment.project_id,
                )
                self.stderr.write(
                    self.style.ERROR(
                        f"Failed processing environment {environment.id}: {e}"
                    )
                )

        queued_projects_count = (
            len(modified_projects) if not dry_run and not skip_recount else 0
        )
        if not dry_run and not skip_recount:
            for project in modified_projects:
                enqueue_membership_refresh(project)
                self.stdout.write(
                    f"Enqueued segment membership refresh for project {project.id}."
                )

        verb = "would be tombstoned" if dry_run else "tombstoned"
        self.stdout.write(
            f"Summary: {scanned_environments} environments scanned, "
            f"{tombstoned_total} identities {verb}, "
            f"{queued_projects_count} projects queued for recount."
        )

        if failed_environments:
            raise CommandError(
                f"Tombstoning failed for environment(s): {failed_environments}"
            )

    @staticmethod
    def _resolve_environments(
        organisation_id: int | None,
        environment_id: int | None,
    ) -> QuerySet[Environment]:
        if organisation_id is not None:
            if not Organisation.objects.filter(id=organisation_id).exists():
                raise CommandError(
                    f"Organisation with id {organisation_id} does not exist."
                )
            return (
                Environment.objects.filter(project__organisation_id=organisation_id)
                .select_related("project", "project__organisation")
                .order_by("id")
            )
        if environment_id is not None:
            if not Environment.objects.filter(id=environment_id).exists():
                raise CommandError(
                    f"Environment with id {environment_id} does not exist."
                )
            return Environment.objects.filter(id=environment_id).select_related(
                "project", "project__organisation"
            )

        seeded_org_ids = SegmentMembershipSeed.objects.filter(
            seeded_at__isnull=False
        ).values_list("organisation_id", flat=True)
        return (
            Environment.objects.filter(project__organisation_id__in=seeded_org_ids)
            .select_related("project", "project__organisation")
            .order_by("id")
        )

    def _process_environment(
        self,
        *,
        environment: Environment,
        env_key: str,
        log_comment: str,
        dry_run: bool,
    ) -> int:
        with open_clickhouse_cursor(log_comment=log_comment) as cursor:
            cursor.execute(_SIZING_SQL, {"env_key": env_key})
            row = cursor.fetchone()
            traitless_count: int = row[0] if row else 0
            if traitless_count == 0:
                return 0
            if dry_run:
                self.stdout.write(
                    f"[DRY RUN] Environment {environment.id} ({env_key}): "
                    f"{traitless_count} traitless identities found."
                )
                return traitless_count
            self.stdout.write(
                f"Environment {environment.id} ({env_key}): "
                f"Tombstoning {traitless_count} traitless identities."
            )
            cursor.execute(_TOMBSTONE_SQL, {"env_key": env_key})
            return traitless_count
