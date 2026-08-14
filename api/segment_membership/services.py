from contextlib import contextmanager
from datetime import datetime
from typing import Any, Iterator

import structlog
from django.db import connections
from django.db.backends.utils import CursorWrapper
from django.db.models import Q
from flag_engine.context.types import EvaluationContext
from flagsmith_sql_flag_engine import (
    Binder,
    PyformatParamStyle,
    TranslateContext,
    translate_segment,
)
from flagsmith_sql_flag_engine.dialects import ClickHouseDialect
from task_processor.models import Task

from environments.models import Environment
from integrations.flagsmith.client import get_openfeature_client
from organisations.models import Organisation
from projects.models import Project
from segment_membership.models import SegmentMembershipCount
from segment_membership.types import ClickHouseReadIdentityRow, SegmentMember
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


def enqueue_membership_refresh(
    project: Project,
    *,
    delay_until: datetime | None = None,
) -> None:
    """Queue a per-project segment membership count refresh.

    Pass `delay_until` to schedule the refresh for a future time, e.g. to let an
    Edge CDC tombstone land in ClickHouse before recounting.

    No-op when the org has the feature off, or when a refresh for the project is
    already pending. A pending refresh scheduled sooner than `delay_until` is
    pushed out to it.
    """
    if not is_membership_enabled(project.organisation):
        return

    from segment_membership.tasks import refresh_project_segment_counts

    pending = Task.objects.filter(
        task_identifier=refresh_project_segment_counts.task_identifier,
        completed=False,
        num_failures__lt=3,
        serialized_args=Task.serialize_data((project.id,)),
    )
    if pending.exists():
        if delay_until is not None:
            pending.filter(
                Q(scheduled_for__isnull=True) | Q(scheduled_for__lt=delay_until),
            ).update(scheduled_for=delay_until)
        return

    refresh_project_segment_counts.delay(
        args=(project.id,),
        delay_until=delay_until,
    )


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
    `project`, scanning each environment once.

    A single `GROUP BY environment_id` over `IDENTITIES FINAL` counts every
    segment in one pass via `countIf(<predicate>)` per segment.

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
    binder = Binder(PyformatParamStyle())
    count_columns: list[str] = []
    counted_segment_ids: list[int] = []
    for seg in segments:
        translate_ctx = TranslateContext(
            evaluation_context=EvaluationContext(
                environment={"key": "_count", "name": project.name}
            ),
            dialect=dialect,
            binder=binder,
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
        count_columns.append(f"countIf({predicate}) AS c{seg.id}")
        counted_segment_ids.append(seg.id)

    if not count_columns:
        return []

    sql = (
        f"SELECT i.environment_id AS env_key, {', '.join(count_columns)} "
        f"FROM IDENTITIES AS i FINAL "
        f"WHERE i.environment_id IN %(env_keys)s AND i.is_deleted = false "
        f"GROUP BY i.environment_id"
    )
    cursor.execute(sql, {"env_keys": tuple(env_id_by_key), **binder.params})
    rows: list[tuple[Any, ...]] = cursor.fetchall()
    membership_counts: list[SegmentMembershipCount] = []
    for row in rows:
        env_id = env_id_by_key.get(str(row[0]))
        if env_id is None:
            continue
        # Columns line up with counted_segment_ids; a zero-match pair is absent.
        for segment_id, count in zip(counted_segment_ids, row[1:]):
            if count:
                membership_counts.append(
                    SegmentMembershipCount(
                        segment_id=segment_id,
                        environment_id=env_id,
                        count=int(count),
                    )
                )
    return membership_counts


def get_segment_members_page(
    segment: Segment,
    environment: Environment,
    *,
    cursor: str | None,
    limit: int,
    q: str | None = None,
) -> list[SegmentMember]:
    """Return one page of identities matching `segment` in `environment`,
    ordered by `identifier`.

    Provide identifier as `cursor` to get a page after that identifier.
    Provide `q` to filter to identifiers containing it (case-insensitive).
    """
    binder = Binder(PyformatParamStyle())
    translate_ctx = TranslateContext(
        evaluation_context=EvaluationContext(
            environment={"key": "_members", "name": segment.project.name}
        ),
        dialect=ClickHouseDialect(),
        binder=binder,
    )
    predicate = translate_segment(
        map_segment_to_segment_context(map_segment_to_engine(segment)),
        translate_ctx,
    )
    if predicate is None:
        logger.error(
            "members.segment.skipped",
            segment__id=segment.id,
            reason="untranslatable",
        )
        return []

    conditions = [
        "i.environment_id = %(env_key)s",
        "i.is_deleted = false",
    ]
    params: dict[str, Any] = {
        "env_key": environment.api_key,
        "limit": limit,
        **binder.params,
    }
    if cursor:
        conditions.append("i.identifier > %(cursor)s")
        params["cursor"] = cursor
    if q:
        conditions.append("positionCaseInsensitiveUTF8(i.identifier, %(q)s) > 0")
        params["q"] = q
    conditions.append(f"({predicate})")

    # Why two queries? `traits` is a wide JSON column split over many per-path files.
    # That fans out into thousands of object-storage requests, which is what
    # makes a cold read slow. Delegating the `traits` read to an outer query
    # limits them to the page.
    #
    # Besides that, bypass FINAL, which is heavy, in favour of LIMIT 1 BY i.identifier,
    # which is (tolerably) less correct but substantially faster.
    inner_sql = (
        "SELECT i.identifier "
        "FROM IDENTITIES AS i "
        f"WHERE {' AND '.join(conditions)} "
        "ORDER BY i.identifier ASC, i.inserted_at DESC "
        "LIMIT 1 BY i.identifier "
        "LIMIT %(limit)s"
    )
    sql = (
        "SELECT m.identifier, m.identity_key, m.traits "
        "FROM IDENTITIES AS m "
        "WHERE m.environment_id = %(env_key)s AND m.is_deleted = false "
        f"AND m.identifier IN ({inner_sql}) "
        "ORDER BY m.identifier ASC, m.inserted_at DESC "
        "LIMIT 1 BY m.identifier"
    )
    log_comment = (
        "flagsmith:segment_membership:read"
        f":org_{segment.project.organisation_id}"
        f":project_{segment.project_id}"
    )
    with open_clickhouse_cursor(log_comment=log_comment) as ch_cursor:
        ch_cursor.execute(sql, params)
        rows: list[ClickHouseReadIdentityRow] = ch_cursor.fetchall()

    return [
        SegmentMember(identifier=row[0], identity_key=row[1], traits=row[2])
        for row in rows
    ]
