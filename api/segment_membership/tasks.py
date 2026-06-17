"""Daily backfill of IDENTITIES from Dynamo to ClickHouse, then per-project
refresh of `SegmentMembershipCount` rows. Each backfill fans out the refresh
so the count read always sees the fresh snapshot. Both tasks short-circuit
when `CLICKHOUSE_ENABLED` is False or the org's `segment_membership_inspection`
flag is off.
"""

from datetime import timedelta
from typing import cast

import structlog
from django.conf import settings
from django.utils import timezone
from flagsmith_schemas.dynamodb import Identity as DynamoIdentity
from task_processor.decorators import (
    register_recurring_task,
    register_task_handler,
)

from environments.dynamodb.wrappers.identity_wrapper import DynamoIdentityWrapper
from projects.models import Project
from segment_membership.mappers import map_identity_document_to_clickhouse_row
from segment_membership.metrics import (
    flagsmith_segment_membership_backfill_duration_seconds,
    flagsmith_segment_membership_backfill_identities_total,
    flagsmith_segment_membership_refresh_duration_seconds,
    flagsmith_segment_membership_refresh_failures_total,
)
from segment_membership.models import SegmentMembershipCount
from segment_membership.services import (
    compute_segment_counts_for_project,
    get_projects_to_process,
    is_membership_enabled,
    open_clickhouse_cursor,
)
from util.util import batched

logger = structlog.get_logger("segment_membership")

# Per-INSERT row count; bounds memory while loading large environments.
_INSERT_BATCH_SIZE = 1000

_IDENTITIES_COLUMN_NAMES = (
    "environment_id",
    "identifier",
    "identity_key",
    "traits",
)

_INSERT_IDENTITIES_SQL = (
    f"INSERT INTO IDENTITIES ({', '.join(_IDENTITIES_COLUMN_NAMES)}) VALUES"
)


@register_recurring_task(
    run_every=timedelta(days=1),
    # 4h fits several large environments back-to-back at SaaS scale.
    timeout=timedelta(hours=4),
)
def backfill_identities_to_clickhouse() -> None:
    """Insert each relevant environment's current Dynamo state into
    IDENTITIES, dispatching one refresh per project as its backfill
    completes so the refresh enqueue rate tracks the backfill rate
    rather than spiking in one burst at the end.
    """
    if not settings.CLICKHOUSE_ENABLED:
        logger.info("backfill.skipped", reason="clickhouse_not_configured")
        return

    wrapper = DynamoIdentityWrapper()
    if not wrapper.is_enabled:
        logger.info("backfill.skipped", reason="dynamo_disabled")
        return

    for project in get_projects_to_process():
        log_comment = (
            "flagsmith:segment_membership:backfill"
            f":org_{project.organisation_id}"
            f":project_{project.id}"
        )
        with open_clickhouse_cursor(log_comment=log_comment) as cursor:
            for env in project.environments.all():
                env_key = env.api_key
                row_count = 0
                try:
                    with flagsmith_segment_membership_backfill_duration_seconds.time():
                        for batch in batched(
                            wrapper.iter_all_items_paginated(env_key),
                            _INSERT_BATCH_SIZE,
                        ):
                            rows = [
                                map_identity_document_to_clickhouse_row(
                                    env_key, cast(DynamoIdentity, doc)
                                )
                                for doc in batch
                            ]
                            # Django's CursorWrapper stub forbids dicts in
                            # the params sequence; clickhouse-driver accepts
                            # them as JSON-column payloads.
                            cursor.executemany(_INSERT_IDENTITIES_SQL, rows)  # type: ignore[arg-type]
                            row_count += len(rows)
                except Exception:
                    logger.exception(
                        "backfill.environment.failed",
                        project__id=project.id,
                        environment__id=env.id,
                    )
                    continue
                flagsmith_segment_membership_backfill_identities_total.inc(row_count)
                logger.info(
                    "backfill.environment.completed",
                    project__id=project.id,
                    environment__id=env.id,
                    rows__count=row_count,
                )
        refresh_project_segment_counts.delay(args=(project.id,))


@register_task_handler(
    # ~2x the expected legitimate ceiling (a single UNION ALL aggregation
    # against IDENTITIES); widen on real data if this starts false-firing.
    timeout=timedelta(minutes=10),
)
def refresh_project_segment_counts(project_id: int) -> None:
    """Compute per-segment match counts for one project and upsert into
    `SegmentMembershipCount`. Re-checks the org flag so a stale fan-out
    skips orgs disabled since dispatch."""
    if not settings.CLICKHOUSE_ENABLED:
        logger.info(
            "refresh.project.skipped",
            project__id=project_id,
            reason="clickhouse_not_configured",
        )
        return

    project = Project.objects.select_related("organisation").get(pk=project_id)
    if not is_membership_enabled(project.organisation):
        logger.info(
            "refresh.project.skipped",
            project__id=project_id,
            reason="ff_disabled",
        )
        return

    log_comment = (
        "flagsmith:segment_membership:refresh"
        f":org_{project.organisation_id}"
        f":project_{project.id}"
    )
    with (
        flagsmith_segment_membership_refresh_duration_seconds.time(),
        open_clickhouse_cursor(log_comment=log_comment) as cursor,
    ):
        try:
            membership_counts = compute_segment_counts_for_project(project, cursor)
        except Exception:
            flagsmith_segment_membership_refresh_failures_total.inc()
            logger.exception("refresh.project.failed", project__id=project_id)
            return

        now = timezone.now()
        for m in membership_counts:
            m.last_synced_at = now

        new_pairs = {(m.segment_id, m.environment_id) for m in membership_counts}
        stale_ids = [
            pk
            for pk, segment_id, environment_id in (
                SegmentMembershipCount.objects.filter(
                    segment__project=project
                ).values_list("id", "segment_id", "environment_id")
            )
            if (segment_id, environment_id) not in new_pairs
        ]
        stale_deleted, _ = SegmentMembershipCount.objects.filter(
            id__in=stale_ids,
        ).delete()

        SegmentMembershipCount.objects.bulk_create(
            membership_counts,
            update_conflicts=True,
            unique_fields=["segment", "environment"],
            update_fields=["count", "last_synced_at"],
        )
        logger.info(
            "refresh.project.completed",
            project__id=project_id,
            membership_counts__count=len(membership_counts),
            stale_counts__count=stale_deleted,
        )
