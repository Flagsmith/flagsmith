from contextlib import contextmanager
from typing import Iterator

import structlog
from django.conf import settings
from flag_engine.context.types import EvaluationContext
from flagsmith_sql_flag_engine import TranslateContext, translate_segment
from flagsmith_sql_flag_engine.dialects import SnowflakeDialect
from snowflake.snowpark import Session

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


def is_snowflake_configured() -> bool:
    """All SNOWFLAKE_* settings required to open a session must be
    populated. Tasks short-circuit when this returns False."""
    return all(
        getattr(settings, name)
        for name in (
            "SNOWFLAKE_ACCOUNT",
            "SNOWFLAKE_USER",
            "SNOWFLAKE_PRIVATE_KEY_PATH",
            "SNOWFLAKE_DATABASE",
            "SNOWFLAKE_SCHEMA",
            "SNOWFLAKE_WAREHOUSE",
        )
    )


@contextmanager
def open_snowflake_session() -> Iterator[Session]:
    """Open a Snowpark session from `SNOWFLAKE_*` settings."""
    config: dict[str, str | None] = {
        "account": settings.SNOWFLAKE_ACCOUNT,
        "user": settings.SNOWFLAKE_USER,
        "warehouse": settings.SNOWFLAKE_WAREHOUSE,
        "database": settings.SNOWFLAKE_DATABASE,
        "schema": settings.SNOWFLAKE_SCHEMA,
        "private_key_file": settings.SNOWFLAKE_PRIVATE_KEY_PATH,
    }
    if settings.SNOWFLAKE_ROLE:
        config["role"] = settings.SNOWFLAKE_ROLE
    sess = Session.builder.configs(config).create()
    try:
        yield sess
    finally:
        sess.close()


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
    project: Project, session: Session
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

    Environment keys are bound as parameters, not f-string-spliced;
    the predicate from `translate_segment` is already escape-safe per
    the SQL flag engine's contract.
    """
    segments = list(Segment.live_objects.filter(project=project))
    env_id_by_key: dict[str, int] = dict(
        project.environments.values_list("api_key", "id"),
    )
    if not segments or not env_id_by_key:
        return []

    env_keys = list(env_id_by_key)
    env_placeholders = ",".join("?" * len(env_keys))
    dialect = SnowflakeDialect()

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
            f"i.environment_id AS env_key, COUNT(*) AS c "
            f"FROM IDENTITIES i "
            f"WHERE i.environment_id IN ({env_placeholders}) AND ({predicate}) "
            f"GROUP BY i.environment_id"
        )

    if not select_clauses:
        return []

    sql = "\nUNION ALL\n".join(select_clauses)
    rows = session.sql(sql, params=env_keys * len(select_clauses)).collect()
    memberships: list[SegmentMembership] = []
    for row in rows:
        env_id = env_id_by_key.get(str(row["ENV_KEY"]))
        if env_id is None:
            continue
        memberships.append(
            SegmentMembership(
                segment_id=int(row["SEGMENT_ID"]),
                environment_id=env_id,
                count=int(row["C"]),
            )
        )
    return memberships
