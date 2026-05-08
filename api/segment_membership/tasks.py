"""Tasks: backfill IDENTITIES from Dynamo to Snowflake daily, then
refresh per-segment counts in the `SegmentMembership` cache.

The backfill recurs daily and, once it finishes, fans out one
`refresh_project_segment_counts` per project — guarantees the refresh
always reads the freshly backfilled snapshot rather than racing a
separate schedule. Both tasks short-circuit when SNOWFLAKE_* settings
are unset, and skip per-organisation when the
`segment_membership_inspection` FoF flag is False.
"""

from datetime import timedelta
from typing import cast

import structlog
from django.utils import timezone
from flagsmith_schemas.dynamodb import Identity as DynamoIdentity
from snowflake.snowpark.types import (
    LongType,
    StringType,
    StructField,
    StructType,
    VariantType,
)
from task_processor.decorators import (
    register_recurring_task,
    register_task_handler,
)

from environments.dynamodb.wrappers.identity_wrapper import DynamoIdentityWrapper
from projects.models import Project
from segment_membership.mappers import map_identity_document_to_snowflake_row
from segment_membership.models import SegmentMembership
from segment_membership.services import (
    compute_segment_counts_for_project,
    get_projects_to_process,
    is_membership_enabled,
    is_snowflake_configured,
    open_snowflake_session,
)
from util.util import batched

logger = structlog.get_logger("segment_membership")

# Per-INSERT row count; bounds memory while loading large environments.
_INSERT_BATCH_SIZE = 1000

_IDENTITIES_SCHEMA = StructType(
    [
        StructField("environment_id", StringType()),
        StructField("id", LongType()),
        StructField("identifier", StringType()),
        StructField("identity_key", StringType()),
        StructField("traits", VariantType()),
    ]
)


@register_recurring_task(
    run_every=timedelta(days=1),
    # The default timeout doesn't fit the per-environment
    # backfill at SaaS scale; 4 hours leaves
    # headroom for several large environments back-to-back without
    # truncating the task processor's lease.
    timeout=timedelta(hours=4),
)
def backfill_identities_to_snowflake() -> None:
    """Replace Snowflake's IDENTITIES rows for every relevant
    environment with the current Dynamo state. Once the backfill
    finishes, fans out one `refresh_project_segment_counts` task per
    project so the count refresh always sees fresh data.

    Per-statement implicit commits leave a brief window where readers
    see an empty partition mid-refresh — a PoC tradeoff later fixed
    by CDC.
    """
    if not is_snowflake_configured():
        logger.info("backfill.skipped", reason="snowflake_not_configured")
        return

    wrapper = DynamoIdentityWrapper()
    if not wrapper.is_enabled:
        logger.info("backfill.skipped", reason="dynamo_disabled")
        return

    refreshable_project_ids: list[int] = []
    with open_snowflake_session() as sess:
        for project in get_projects_to_process():
            refreshable_project_ids.append(project.id)
            for env in project.environments.all():
                env_key = env.api_key
                row_count = 0
                try:
                    sess.sql(
                        "DELETE FROM IDENTITIES WHERE environment_id = ?",
                        params=[env_key],
                    ).collect()
                    for batch in batched(
                        wrapper.iter_all_items_paginated(env_key),
                        _INSERT_BATCH_SIZE,
                    ):
                        rows = [
                            map_identity_document_to_snowflake_row(
                                env_key, cast(DynamoIdentity, doc)
                            )
                            for doc in batch
                        ]
                        sess.create_dataframe(
                            rows, schema=_IDENTITIES_SCHEMA
                        ).write.mode("append").save_as_table("IDENTITIES")
                        row_count += len(rows)
                except Exception:
                    logger.exception(
                        "backfill.environment.failed",
                        project__id=project.id,
                        environment__id=env.id,
                    )
                    continue
                logger.info(
                    "backfill.environment.completed",
                    project__id=project.id,
                    environment__id=env.id,
                    rows__count=row_count,
                )

    for project_id in refreshable_project_ids:
        refresh_project_segment_counts.delay(args=(project_id,))


@register_task_handler(
    # One project's predicate matrix at SaaS scale takes seconds to a
    # few minutes; 30 minutes bounds runaway queries without cutting
    # legitimate ones short.
    timeout=timedelta(minutes=30),
)
def refresh_project_segment_counts(project_id: int) -> None:
    """Compute per-segment match counts for a single project and upsert
    into `SegmentMembership`. Re-checks the FoF flag at execution time
    so a stale fan-out skips orgs that have since been disabled."""
    if not is_snowflake_configured():
        logger.info(
            "refresh.project.skipped",
            project__id=project_id,
            reason="snowflake_not_configured",
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

    with open_snowflake_session() as sess:
        try:
            memberships = compute_segment_counts_for_project(project, sess)
        except Exception:
            logger.exception("refresh.project.failed", project__id=project_id)
            return

        now = timezone.now()
        for m in memberships:
            m.last_synced_at = now
        SegmentMembership.objects.bulk_create(
            memberships,
            update_conflicts=True,
            unique_fields=["segment", "environment"],
            update_fields=["count", "last_synced_at"],
        )
        logger.info(
            "refresh.project.completed",
            project__id=project_id,
            memberships__count=len(memberships),
        )
