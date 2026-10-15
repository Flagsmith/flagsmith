from argparse import ArgumentParser
from collections import Counter
from typing import Any

import structlog
from django.core.management import BaseCommand, CommandError

from edge_api.identities.edge_identity_service import (
    delete_orphaned_identity_override,
    iter_orphaned_identity_overrides,
)
from environments.models import Environment

logger: structlog.BoundLogger = structlog.get_logger("edge_identities")


class Command(BaseCommand):
    help = (
        "Delete identity overrides in the environments_v2 table that the identity "
        "they belong to no longer has, so that local evaluation and the dashboard "
        "agree with the identity document."
    )

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--environment-id",
            dest="environment_id",
            type=int,
            required=True,
            help="ID of the environment to reconcile",
        )
        parser.add_argument(
            "--dry-run",
            dest="dry_run",
            action="store_true",
            help="Report what would be deleted without deleting anything",
        )

    def handle(
        self,
        *args: Any,
        environment_id: int,
        dry_run: bool,
        **options: Any,
    ) -> None:
        try:
            environment = Environment.objects.get(id=environment_id)
        except Environment.DoesNotExist:
            raise CommandError(f"Environment {environment_id} does not exist")

        log: structlog.BoundLogger = logger.bind(  # type: ignore[assignment]
            environment__id=environment.id,
            dry_run=dry_run,
        )
        log.info("identity_override.reconciliation_started")

        reasons: Counter[str] = Counter()
        deleted_count = skipped_count = 0

        for orphaned_identity_override in iter_orphaned_identity_overrides(environment):
            reasons[orphaned_identity_override.reason.value] += 1
            self.stdout.write(
                "\t".join(
                    [
                        orphaned_identity_override.reason.value,
                        orphaned_identity_override.feature_name,
                        orphaned_identity_override.identifier,
                        orphaned_identity_override.document_key,
                    ]
                )
            )
            if dry_run:
                continue
            if delete_orphaned_identity_override(
                environment_id=environment.id,
                orphaned_identity_override=orphaned_identity_override,
            ):
                deleted_count += 1
            else:
                # The override was rewritten between being read and being
                # deleted, so it is no longer the stale document we identified.
                skipped_count += 1
                log.info(
                    "identity_override.delete_skipped",
                    document_key=orphaned_identity_override.document_key,
                )

        log.info(
            "identity_override.reconciliation_finished",
            orphaned__count=sum(reasons.values()),
            deleted__count=deleted_count,
            skipped__count=skipped_count,
            reasons=dict(reasons),
        )
