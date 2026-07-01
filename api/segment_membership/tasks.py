from datetime import timedelta
from typing import cast

import structlog
from django.conf import settings
from django.db.models import Exists, OuterRef
from django.utils import timezone
from flagsmith_schemas.dynamodb import Identity as DynamoIdentity
from task_processor.decorators import (
    register_recurring_task,
    register_task_handler,
)
from task_processor.models import Task

from environments.dynamodb.wrappers.identity_wrapper import DynamoIdentityWrapper
from organisations.models import Organisation
from projects.models import Project
from segment_membership.mappers import map_identity_document_to_clickhouse_row
from segment_membership.metrics import (
    flagsmith_segment_membership_backfill_duration_seconds,
    flagsmith_segment_membership_backfill_identities_total,
    flagsmith_segment_membership_refresh_duration_seconds,
    flagsmith_segment_membership_refresh_failures_total,
)
from segment_membership.models import SegmentMembershipCount, SegmentMembershipSeed
from segment_membership.services import (
    compute_segment_counts_for_project,
    enqueue_membership_refresh,
    get_projects_to_process,
    is_membership_enabled,
    open_clickhouse_cursor,
)
from segments.models import Segment
from util.util import batched

logger = structlog.get_logger("segment_membership")

# Per-INSERT row count; bounds memory while loading large environments.
_INSERT_BATCH_SIZE = 1000

_IDENTITIES_COLUMN_NAMES = (
    "environment_id",
    "identifier",
    "identity_key",
    "traits",
    "inserted_at",
)

_INSERT_IDENTITIES_SQL = (
    f"INSERT INTO IDENTITIES ({', '.join(_IDENTITIES_COLUMN_NAMES)}) VALUES"
)


@register_task_handler(
    # 4h fits several large environments back-to-back at SaaS scale.
    timeout=timedelta(hours=4),
)
def seed_organisation_identities(organisation_id: int) -> None:
    """Mirror one organisation's current Dynamo identities into IDENTITIES,
    dispatching a refresh per project as each completes.

    Rows are versioned at scan start via `inserted_at`
    so writes arriving mid-scan win ReplacingMergeTree dedup over the seeded row.
    """
    log = logger.bind(organisation__id=organisation_id)
    if not settings.CLICKHOUSE_ENABLED:
        log.warning("seed.skipped", reason="clickhouse_not_configured")
        return

    organisation = Organisation.objects.get(pk=organisation_id)
    if not is_membership_enabled(organisation):
        log.info("seed.skipped", reason="ff_disabled")
        return

    wrapper = DynamoIdentityWrapper()
    if not wrapper.is_enabled:
        log.warning("seed.skipped", reason="dynamo_disabled")
        return

    scan_started_at = timezone.now()
    projects_with_live_segments = Project.objects.filter(
        organisation=organisation,
    ).filter(Exists(Segment.live_objects.filter(project=OuterRef("pk"))))
    for project in projects_with_live_segments:
        log_comment = (
            "flagsmith:segment_membership:backfill"
            f":org_{organisation_id}"
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
                                    env_key,
                                    cast(DynamoIdentity, doc),
                                    scan_started_at,
                                )
                                for doc in batch
                            ]
                            # Django's CursorWrapper stub forbids dicts in
                            # the params sequence; clickhouse-driver accepts
                            # them as JSON-column payloads.
                            cursor.executemany(_INSERT_IDENTITIES_SQL, rows)  # type: ignore[arg-type]
                            row_count += len(rows)
                except Exception:
                    log.exception(
                        "seed.environment.failed",
                        project__id=project.id,
                        environment__id=env.id,
                    )
                    continue
                flagsmith_segment_membership_backfill_identities_total.inc(row_count)
                log.info(
                    "seed.environment.completed",
                    project__id=project.id,
                    environment__id=env.id,
                    rows__count=row_count,
                )
        enqueue_membership_refresh(project)

    SegmentMembershipSeed.objects.update_or_create(
        organisation=organisation,
        defaults={"seeded_at": timezone.now()},
    )


# TODO https://github.com/Flagsmith/flagsmith/issues/7917
@register_recurring_task(
    run_every=timedelta(hours=1),
    timeout=timedelta(minutes=5),
)
def reconcile_segment_membership_seeds() -> None:
    """Enqueue a backfill for each opted-in organisation that owns live
    segments and hasn't been seeded yet, debouncing orgs whose seed is already
    pending.
    """
    if not settings.CLICKHOUSE_ENABLED:
        return

    seeded_organisation_ids = set(
        SegmentMembershipSeed.objects.filter(seeded_at__isnull=False).values_list(
            "organisation_id", flat=True
        )
    )
    organisation_ids = {
        project.organisation_id for project in get_projects_to_process()
    } - seeded_organisation_ids

    for organisation_id in organisation_ids:
        if Task.objects.filter(
            task_identifier=seed_organisation_identities.task_identifier,
            completed=False,
            num_failures__lt=3,
            serialized_args=Task.serialize_data((organisation_id,)),
        ).exists():
            continue
        seed_organisation_identities.delay(args=(organisation_id,))


@register_recurring_task(
    run_every=timedelta(hours=settings.SEGMENT_MEMBERSHIP_REFRESH_INTERVAL_HOURS),
    timeout=timedelta(minutes=10),
)
def refresh_all_segment_counts() -> None:
    """Refresh counts for every project with a live segment"""
    if not settings.CLICKHOUSE_ENABLED:
        return

    project_ids = Segment.live_objects.values_list("project_id", flat=True)
    for project in (
        Project.objects.filter(id__in=project_ids)
        .select_related("organisation")
        .iterator()
    ):
        enqueue_membership_refresh(project)


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
