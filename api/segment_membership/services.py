from contextlib import contextmanager
from typing import Any, Iterator

import structlog
from django.db import connections
from django.db.backends.utils import CursorWrapper
from flag_engine.context.types import EvaluationContext
from flagsmith_sql_flag_engine import TranslateContext, translate_segment
from flagsmith_sql_flag_engine.dialects import ClickHouseDialect
from task_processor.models import Task

from integrations.flagsmith.client import get_openfeature_client
from organisations.models import Organisation
from projects.models import Project
from segment_membership.models import SegmentMembershipCount
from segments.models import Segment
from util.engine_models.context.mappers import map_segment_to_segment_context
from util.mappers.engine import map_segment_to_engine

logger = structlog.get_logger("segment_membership")


def is_membership_enabled(organisation: Organisation) -> bool:
    """Resolve the per-org segment-membership inspection flag, default False."""
    return get_openfeature_client().get_boolean_value(
        "segment_membership_inspection",
        default_value=False,
        evaluation_context=organisation.openfeature_evaluation_context,
    )


def enqueue_membership_refresh(project: Project) -> None:
    """Queue a per-project segment membership count refresh after a canonical
    segment is created or edited.

    No-op when the org has the feature off, or when a refresh for the project
    is already pending or running.
    """
    if not is_membership_enabled(project.organisation):
        return

    from segment_membership.tasks import refresh_project_segment_counts

    if Task.objects.filter(
        task_identifier=refresh_project_segment_counts.task_identifier,
        completed=False,
        num_failures__lt=3,
        serialized_args=Task.serialize_data((project.id,)),
    ).exists():
        return

    refresh_project_segment_counts.delay(args=(project.id,))


@contextmanager
def open_clickhouse_cursor(
    *, log_comment: str | None = None
) -> Iterator[CursorWrapper]:
    """Yield a cursor bound to the `clickhouse` database alias.

    `log_comment` lands on every query as a session setting so CH's
    `system.query_log` carries per-org / per-project attribution.
    """
    with connections["clickhouse"].cursor() as cursor:
        if log_comment:
            # Underlying clickhouse-driver cursor exposes set_settings(...).
            cursor.cursor.set_settings({"log_comment": log_comment})
        yield cursor


def get_projects_to_process() -> Iterator[Project]:
    """Yield projects with at least one canonical segment whose org has
    the segment-membership flag on."""
    project_ids = Segment.live_objects.values_list("project_id", flat=True)
    projects_with_live_segments = (
        Project.objects.filter(id__in=project_ids)
        .select_related("organisation")
        .iterator()
    )
    for project in projects_with_live_segments:
        if not is_membership_enabled(project.organisation):
            continue
        yield project


def compute_segment_counts_for_project(
    project: Project, cursor: CursorWrapper
) -> list[SegmentMembershipCount]:
    """Count identity matches per (canonical-segment, environment) for
    `project` in one `UNION ALL` query.

    Returns unsaved `SegmentMembershipCount` instances with `count` and
    keys populated; the caller stamps `last_synced_at` consistently
    across the batch. Untranslatable segments and pairs with zero
    matches are absent from the result. `FROM IDENTITIES FINAL` forces
    ReplacingMergeTree to dedupe at read time so counts reflect the
    most-recent backfill regardless of merge state.
    """
    segments = list(Segment.live_objects.filter(project=project))
    env_id_by_key: dict[str, int] = dict(
        project.environments.values_list("api_key", "id"),
    )
    if not segments or not env_id_by_key:
        return []

    dialect = ClickHouseDialect()
    select_clauses: list[str] = []
    for seg in segments:
        translate_ctx = TranslateContext(
            evaluation_context=EvaluationContext(
                environment={"key": "_count", "name": project.name}
            ),
            dialect=dialect,
        )
        predicate = translate_segment(
            map_segment_to_segment_context(map_segment_to_engine(seg)),
            translate_ctx,
        )
        if predicate is None:
            logger.error(
                "compute.segment.skipped",
                project__id=project.id,
                segment__id=seg.id,
                reason="untranslatable",
            )
            continue
        select_clauses.append(
            f"SELECT {seg.id} AS segment_id, "
            f"i.environment_id AS env_key, count() AS c "
            f"FROM IDENTITIES AS i FINAL "
            f"WHERE i.environment_id IN %(env_keys)s AND ({predicate}) "
            f"GROUP BY i.environment_id"
        )

    if not select_clauses:
        return []

    sql = "\nUNION ALL\n".join(select_clauses)
    cursor.execute(sql, {"env_keys": tuple(env_id_by_key)})
    rows: list[tuple[Any, ...]] = cursor.fetchall()
    membership_counts: list[SegmentMembershipCount] = []
    for row in rows:
        env_id = env_id_by_key.get(str(row[1]))
        if env_id is None:
            continue
        membership_counts.append(
            SegmentMembershipCount(
                segment_id=int(row[0]),
                environment_id=env_id,
                count=int(row[2]),
            )
        )
    return membership_counts
