from contextlib import contextmanager
from typing import Iterator

import clickhouse_connect
import structlog
from clickhouse_connect.driver import Client
from django.conf import settings
from flag_engine.context.types import EvaluationContext
from flagsmith_sql_flag_engine import TranslateContext, translate_segment
from flagsmith_sql_flag_engine.dialects import ClickHouseDialect

from integrations.flagsmith.client import get_openfeature_client
from organisations.models import Organisation
from projects.models import Project
from segment_membership.models import SegmentMembership
from segments.models import Segment
from util.engine_models.context.mappers import map_segment_to_segment_context
from util.mappers.engine import map_segment_to_engine

logger = structlog.get_logger("segment_membership")


def is_membership_enabled(organisation: Organisation) -> bool:
    """Resolve the per-org Flagsmith-on-Flagsmith flag for segment-
    membership inspection. Defaults False when the flag is missing."""
    return get_openfeature_client().get_boolean_value(
        "segment_membership_inspection",
        default_value=False,
        evaluation_context=organisation.openfeature_evaluation_context,
    )


def is_clickhouse_configured() -> bool:
    """Either `CLICKHOUSE_URL` (DSN) or `CLICKHOUSE_HOST` gates the
    feature — every other CLICKHOUSE_* setting has a sensible default.
    Tasks short-circuit when this returns False."""
    return bool(settings.CLICKHOUSE_URL or settings.CLICKHOUSE_HOST)


@contextmanager
def open_clickhouse_client(*, log_comment: str | None = None) -> Iterator[Client]:
    """Open a clickhouse-connect client from `CLICKHOUSE_*` settings.

    `log_comment` lands on every query the client runs as a
    `log_comment` session setting; it's our spend-attribution analogue
    of Snowflake's `QUERY_TAG` and shows up in `system.query_log` for
    per-org / per-project rollups.
    """
    client_settings: dict[str, str | int] = {
        # Required for `JSON`-column DDL on ClickHouse Cloud as of 25.12.
        # No-op on OSS builds where the type is already GA.
        "allow_experimental_json_type": 1,
    }
    if log_comment:
        client_settings["log_comment"] = log_comment
    # clickhouse-connect's per-field args take precedence over the DSN's
    # parsed values (`port = port or parsed.port`), so when CLICKHOUSE_URL
    # is set we hand off the DSN exclusively and let it drive every field.
    if settings.CLICKHOUSE_URL:
        client = clickhouse_connect.get_client(
            dsn=settings.CLICKHOUSE_URL,
            settings=client_settings,
        )
    else:
        client = clickhouse_connect.get_client(
            host=settings.CLICKHOUSE_HOST,
            port=settings.CLICKHOUSE_PORT,
            username=settings.CLICKHOUSE_USER,
            password=settings.CLICKHOUSE_PASSWORD,
            database=settings.CLICKHOUSE_DATABASE,
            secure=settings.CLICKHOUSE_SECURE,
            settings=client_settings,
        )
    try:
        yield client
    finally:
        client.close()


def get_projects_to_process() -> Iterator[Project]:
    """Yield projects that hold at least one canonical segment and whose
    organisation has the segment-membership FoF flag enabled. Used by
    both the backfill and refresh tasks to scope work."""
    project_ids = Segment.live_objects.values_list("project_id", flat=True).distinct()
    for project in Project.objects.filter(id__in=project_ids).select_related(
        "organisation"
    ):
        if not is_membership_enabled(project.organisation):
            continue
        yield project


def compute_segment_counts_for_project(
    project: Project, client: Client
) -> list[SegmentMembership]:
    """Run one batched `SELECT ... UNION ALL` counting identity matches
    for every (canonical-segment, environment) pair in `project`.

    Returns a list of unsaved `SegmentMembership` instances — `count`
    and the `(segment_id, environment_id)` keys are populated;
    `last_synced_at` is left for the caller to stamp consistently
    across the batch.

    The SQL groups by `environment_id` per segment, so cardinality is
    one SELECT per segment rather than per (segment, env) pair. Pairs
    with zero matches are absent from the result; the caller treats
    absent pairs as "no row" rather than count = 0.

    Segments whose predicate is currently untranslatable — e.g. a
    regex pattern unsupported by the active dialect — are skipped
    entirely.

    Environment keys are bound as a named array parameter; the
    predicate from `translate_segment` is already escape-safe per the
    SQL flag engine's contract.

    The `FROM IDENTITIES FINAL` keyword forces ReplacingMergeTree to
    dedupe rows at query time. Counts are read strictly against the
    most-recent backfill, regardless of how many merge passes have
    happened since.
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
            f"WHERE i.environment_id IN {{env_keys:Array(String)}} AND ({predicate}) "
            f"GROUP BY i.environment_id"
        )

    if not select_clauses:
        return []

    sql = "\nUNION ALL\n".join(select_clauses)
    result = client.query(sql, parameters={"env_keys": list(env_id_by_key)})
    memberships: list[SegmentMembership] = []
    for row in result.result_rows:
        env_id = env_id_by_key.get(str(row[1]))
        if env_id is None:
            continue
        memberships.append(
            SegmentMembership(
                segment_id=int(row[0]),
                environment_id=env_id,
                count=int(row[2]),
            )
        )
    return memberships
