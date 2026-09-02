from __future__ import annotations

import hashlib
import json
import time
import typing
from dataclasses import replace
from functools import lru_cache

import structlog
from clickhouse_connect.driver.exceptions import ClickHouseError
from clickhouse_driver import Client
from clickhouse_driver.util.helpers import parse_url
from django.conf import settings
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone
from flag_engine.segments.constants import ALL_RULE, ANY_RULE, PERCENTAGE_SPLIT
from rest_framework.exceptions import ValidationError

from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from cohorts.models import Cohort
from core.dataclasses import AuthorData
from environments.tasks import rebuild_environment_document
from experimentation import warehouse_delivery_service
from experimentation.constants import (
    CONTROL_VARIANT_KEY,
    EXPERIMENT_FLAG,
    EXPOSURE_HOURLY_BUCKET_MAX_WINDOW,
    MAX_AUDIENCE_SEGMENTS,
    RESULTS_MIN_CONVERSIONS_PER_VARIANT,
    RESULTS_MIN_IDENTITIES_PER_VARIANT,
    SRM_MIN_TOTAL_IDENTITIES,
    WAREHOUSE_CONNECTION_FLAG,
)
from experimentation.dataclasses import (
    AudienceSpec,
    ConversionBucket,
    ConversionsTimeseries,
    ConversionsTimeseriesPoint,
    ExposureBucket,
    ExposuresSummary,
    ExposuresTimeseries,
    ExposuresTimeseriesPoint,
    MetricResult,
    MetricSpec,
    ResultsAggregates,
    ResultsSummary,
    RolloutSpec,
    WarehouseEventNames,
    WarehouseEventStats,
)
from experimentation.metrics import (
    flagsmith_experimentation_warehouse_connection_verifications_total,
    flagsmith_experimentation_warehouse_delivery_objects_total,
    flagsmith_experimentation_warehouse_delivery_runs_total,
)
from experimentation.models import (
    VALID_STATUS_TRANSITIONS,
    AudienceMatch,
    Experiment,
    ExperimentStatus,
    MetricAggregation,
    MetricDirection,
    WarehouseConnection,
    WarehouseConnectionStatus,
    WarehouseDeliveryLog,
    WarehouseDeliveryOutcome,
    WarehouseType,
)
from experimentation.results_query import (
    _EXPOSURES_CTE,
    ResultsQueryBuilder,
    exposure_window_params,
)
from experimentation.stats import (
    Inference,
    VariantStats,
    compare_to_control,
    srm_p_value,
)
from features.feature_states.models import API_VALUE_TYPES
from features.models import FeatureState
from features.value_types import BOOLEAN, STRING
from features.versioning.dataclasses import FlagChangeSet, MultivariateValueChangeSet
from features.versioning.versioning_service import (
    get_environment_flags_list,
    update_flag,
    update_multivariate_values,
)
from integrations.flagsmith.client import get_openfeature_client
from segments.models import Condition, Segment, SegmentRule

# TODO: Delete alias as per https://github.com/Flagsmith/flagsmith/issues/7818
from segments.types import SegmentRule as SegmentRuleType

if typing.TYPE_CHECKING:
    from collections.abc import Sequence
    from datetime import datetime

    from clickhouse_connect.driver.client import Client as ClickHouseHTTPClient
    from flag_engine.segments.types import ConditionOperator, RuleType

    from environments.models import Environment
    from experimentation.models import Metric
    from experimentation.types import (
        AudienceSegmentSnapshot,
        AudienceSnapshot,
        ExposureGranularity,
    )
    from features.feature_states.models import FeatureValueType
    from features.models import FeatureStateValue
    from organisations.models import Organisation
    from users.models import FFAdminUser

logger = structlog.get_logger("warehouse")
experimentation_logger = structlog.get_logger("experimentation")

CLICKHOUSE_CONNECT_TIMEOUT_SECONDS = 5
CLICKHOUSE_QUERY_TIMEOUT_SECONDS = 30
CLICKHOUSE_BACKGROUND_QUERY_TIMEOUT_SECONDS = 120
CLICKHOUSE_VERIFY_TIMEOUT_SECONDS = 5
CLICKHOUSE_EVENT_NAMES_TIMEOUT_SECONDS = 15
CUSTOMER_EVENT_STATS_CACHE_SECONDS = 60
EVENT_NAMES_CACHE_SECONDS = 300
CUSTOMER_EVENT_NAMES_FAILURE_CACHE_SECONDS = 60
WAREHOUSE_EVENT_NAMES_LIMIT = 500

_CUSTOMER_EVENT_UNAVAILABLE = "unavailable"


def _customer_cache_key(kind: str, connection: "WarehouseConnection") -> str:
    """Key cached warehouse reads by the connection's non-secret details, so a
    config or type change can neither serve nor store stale reads. Credentials
    stay out of the key material: they don't determine what the warehouse
    holds, so rotating them keeps the cache valid."""
    details = json.dumps(
        [connection.warehouse_type, connection.config],
        sort_keys=True,
    )
    digest = hashlib.sha256(details.encode()).hexdigest()[:12]
    return f"experimentation:customer_{kind}:{connection.id}:{digest}"


# A delivery run stops taking on new objects after this long, leaving room for
# the slowest possible in-flight insert to still land inside the task timeout.
DELIVERY_TIME_BUDGET_SECONDS = 210


def is_warehouse_feature_enabled(organisation: Organisation) -> bool:
    return get_openfeature_client().get_boolean_value(
        WAREHOUSE_CONNECTION_FLAG,
        default_value=False,
        evaluation_context=organisation.openfeature_evaluation_context,
    )


def is_experiment_feature_enabled(organisation: Organisation) -> bool:
    return get_openfeature_client().get_boolean_value(
        EXPERIMENT_FLAG,
        default_value=False,
        evaluation_context=organisation.openfeature_evaluation_context,
    )


def get_experiment_flag_config(
    organisation: Organisation,
) -> dict[str, object]:
    if not is_experiment_feature_enabled(organisation):
        return {}
    raw = get_openfeature_client().get_string_value(
        EXPERIMENT_FLAG,
        default_value="{}",
        evaluation_context=organisation.openfeature_evaluation_context,
    )
    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def ensure_flagsmith_warehouse_connection(
    environment: Environment,
) -> WarehouseConnection | None:
    config = get_experiment_flag_config(environment.project.organisation)
    if not config.get("auto_connect_warehouse"):
        return None

    if WarehouseConnection.objects.filter(
        environment=environment,
        deleted_at__isnull=True,
    ).exists():
        return None

    try:
        connection: WarehouseConnection = WarehouseConnection.objects.create(
            environment=environment,
            warehouse_type=WarehouseType.FLAGSMITH,
            name="Flagsmith",
        )
        return connection
    except IntegrityError:
        return None


@lru_cache(maxsize=2)
def _get_clickhouse_client(
    send_receive_timeout: int = CLICKHOUSE_QUERY_TIMEOUT_SECONDS,
) -> Client:
    """Build a clickhouse-driver client for the experimentation event store.

    The database is taken from the DSN path, so queries can reference the
    `events` table unqualified. Connect and query timeouts are bounded unless the
    DSN overrides them. One client is cached per requested timeout.
    """
    host, kwargs = parse_url(settings.EXPERIMENTATION_CLICKHOUSE_URL)
    kwargs.setdefault("connect_timeout", CLICKHOUSE_CONNECT_TIMEOUT_SECONDS)
    kwargs.setdefault("send_receive_timeout", send_receive_timeout)
    kwargs.setdefault("client_name", settings.CLICKHOUSE_CONNECTION_CLIENT_NAME)
    return Client(host, **kwargs)


_CLICKHOUSE_EVENT_NAMES_QUERY = (
    "SELECT event FROM events "
    "WHERE environment_key = %(environment_key)s "
    "GROUP BY event ORDER BY max(timestamp) DESC LIMIT %(limit)s"
)


def _event_names_query_params(environment_key: str) -> dict[str, str | int]:
    # Fetch one row past the limit so truncation is detectable.
    return {
        "environment_key": environment_key,
        "limit": WAREHOUSE_EVENT_NAMES_LIMIT + 1,
    }


def _build_event_names(
    rows: "Sequence[Sequence[typing.Any]]",
) -> WarehouseEventNames:
    names = [event for (event,) in rows]
    return WarehouseEventNames(
        events=names[:WAREHOUSE_EVENT_NAMES_LIMIT],
        is_truncated=len(names) > WAREHOUSE_EVENT_NAMES_LIMIT,
    )


EVENT_NAMES_SUPPORTED_WAREHOUSE_TYPES = (
    WarehouseType.FLAGSMITH,
    WarehouseType.CLICKHOUSE,
)


def get_warehouse_event_names(
    connection: "WarehouseConnection",
    environment_key: str,
) -> WarehouseEventNames | None:
    if connection.warehouse_type == WarehouseType.CLICKHOUSE:
        return _get_customer_clickhouse_event_names(connection, environment_key)
    if connection.warehouse_type == WarehouseType.FLAGSMITH:
        return _get_flagsmith_clickhouse_event_names(environment_key)
    raise ValueError(f"Unsupported warehouse type: {connection.warehouse_type}")


def _get_flagsmith_clickhouse_event_names(
    environment_key: str,
) -> WarehouseEventNames | None:
    if not settings.EXPERIMENTATION_CLICKHOUSE_URL:
        return None
    cache_key = f"experimentation:event_names:{environment_key}"
    cached = cache.get(cache_key)
    if isinstance(cached, WarehouseEventNames):
        return cached
    try:
        rows = _get_clickhouse_client().execute(
            _CLICKHOUSE_EVENT_NAMES_QUERY,
            _event_names_query_params(environment_key),
        )
    except Exception:
        logger.warning(
            "connection.event_names_failed",
            environment__key=environment_key,
            exc_info=True,
        )
        return None
    event_names = _build_event_names(rows)
    cache.set(cache_key, event_names, EVENT_NAMES_CACHE_SECONDS)
    return event_names


_EVENT_STATS_QUERY = (
    "SELECT count() AS total, uniqExact(event) AS unique "
    "FROM events WHERE environment_key = %(environment_key)s"
)


def _build_event_stats(
    rows: Sequence[Sequence[typing.Any]],
) -> WarehouseEventStats:
    total, unique = rows[0] if rows else (0, 0)
    return WarehouseEventStats(
        total_events_received=int(total),
        unique_events_count=int(unique),
    )


def get_warehouse_event_stats(environment_key: str) -> WarehouseEventStats:
    """Return event counts recorded for `environment_key` in the warehouse."""
    rows = _get_clickhouse_client().execute(
        _EVENT_STATS_QUERY,
        {"environment_key": environment_key},
    )
    return _build_event_stats(rows)


EXPOSURE_BUCKETS_QUERY = (
    _EXPOSURES_CTE
    + """
SELECT
    quarantined,
    variant,
    {bucket_function}(first_exposure, 'UTC') AS bucket,
    count() AS first_exposed_identities
FROM exposures
GROUP BY quarantined, variant, bucket
ORDER BY bucket
"""
)

_EXPOSURE_BUCKET_FUNCTIONS: dict[str, str] = {
    "hour": "toStartOfHour",
    "day": "toStartOfDay",
}


def compute_exposures_summary(
    *,
    environment_key: str,
    feature_name: str,
    window_start: datetime,
    window_end: datetime,
) -> ExposuresSummary:
    granularity = _select_exposure_granularity(window_start, window_end)
    buckets = get_exposure_buckets(
        environment_key=environment_key,
        feature_name=feature_name,
        window_start=window_start,
        window_end=window_end,
        granularity=granularity,
    )
    return build_exposures_summary(buckets, granularity=granularity)


def build_exposures_summary(
    buckets: Sequence[ExposureBucket],
    *,
    granularity: ExposureGranularity,
) -> ExposuresSummary:
    return ExposuresSummary(
        excluded_identities=sum(
            b.first_exposed_identities for b in buckets if b.quarantined
        ),
        timeseries=_exposures_timeseries(buckets, granularity=granularity),
    )


def _exposures_timeseries(
    buckets: Sequence[ExposureBucket],
    *,
    granularity: ExposureGranularity,
) -> ExposuresTimeseries:
    return ExposuresTimeseries(
        granularity=granularity,
        points=[
            ExposuresTimeseriesPoint(bucket=bucket, new_identities=counts)
            for bucket, counts in _counts_by_bucket(
                (b.bucket, b.variant, b.first_exposed_identities)
                for b in buckets
                if not b.quarantined
            )
        ],
    )


def _conversions_timeseries(
    metric_id: int,
    aggregates: ResultsAggregates,
) -> ConversionsTimeseries | None:
    buckets = aggregates.conversion_buckets.get(metric_id)
    if buckets is None:
        return None
    return ConversionsTimeseries(
        granularity=aggregates.granularity,
        points=[
            ConversionsTimeseriesPoint(bucket=bucket, converted_identities=counts)
            for bucket, counts in _counts_by_bucket(
                (b.bucket, b.variant, b.converted_identities) for b in buckets
            )
        ],
    )


def _counts_by_bucket(
    rows: typing.Iterable[tuple[datetime, str, int]],
) -> list[tuple[str, dict[str, int]]]:
    """Group rows into one per-variant dict per bucket, in bucket order. The
    bucket becomes an ISO string because the summary lands in a JSONField as
    is, and datetimes wouldn't serialise."""
    counts_by_bucket: dict[datetime, dict[str, int]] = {}
    for bucket, variant, count in rows:
        counts_by_bucket.setdefault(bucket, {})[variant] = count
    return [
        (bucket.isoformat(), counts_by_bucket[bucket])
        for bucket in sorted(counts_by_bucket)
    ]


def _select_exposure_granularity(
    window_start: datetime,
    window_end: datetime,
) -> ExposureGranularity:
    if window_end - window_start <= EXPOSURE_HOURLY_BUCKET_MAX_WINDOW:
        return "hour"
    return "day"


def get_exposure_buckets(
    *,
    environment_key: str,
    feature_name: str,
    window_start: datetime,
    window_end: datetime,
    granularity: ExposureGranularity,
) -> list[ExposureBucket]:
    rows = _get_clickhouse_client(
        send_receive_timeout=CLICKHOUSE_BACKGROUND_QUERY_TIMEOUT_SECONDS,
    ).execute(
        EXPOSURE_BUCKETS_QUERY.format(
            bucket_function=_EXPOSURE_BUCKET_FUNCTIONS[granularity]
        ),
        exposure_window_params(
            environment_key=environment_key,
            feature_name=feature_name,
            window_start=window_start,
            window_end=window_end,
        ),
    )
    return [
        ExposureBucket(
            variant=variant,
            bucket=bucket,
            first_exposed_identities=int(first_exposed_identities),
            quarantined=bool(quarantined),
        )
        for quarantined, variant, bucket, first_exposed_identities in rows
    ]


def get_results_aggregates(
    *,
    environment_key: str,
    feature_name: str,
    window_start: datetime,
    window_end: datetime,
    specs: Sequence[MetricSpec],
    granularity: ExposureGranularity,
) -> ResultsAggregates:
    """Run the warehouse reads behind one results refresh: per-variant identity
    counts and sufficient statistics, exposure buckets, and per charted metric
    the buckets of first post-exposure conversions.

    Three separate reads, so events landing mid-run can leave the chart's last
    point a few identities off the table until the next refresh."""
    builder = ResultsQueryBuilder(specs)
    params = builder.params(
        environment_key=environment_key,
        feature_name=feature_name,
        window_start=window_start,
        window_end=window_end,
    )
    client = _get_clickhouse_client(
        send_receive_timeout=CLICKHOUSE_BACKGROUND_QUERY_TIMEOUT_SECONDS,
    )

    rows, columns = client.execute(
        builder.build_query(), params, with_column_types=True
    )
    exposure_counts, metric_stats = builder.decode_rows(
        rows, [name for name, _type in columns]
    )

    conversion_buckets: dict[int, list[ConversionBucket]] = {}
    conversions_query = builder.build_conversions_query(
        bucket_function=_EXPOSURE_BUCKET_FUNCTIONS[granularity]
    )
    if conversions_query is not None:
        rows, columns = client.execute(
            conversions_query, params, with_column_types=True
        )
        conversion_buckets = builder.decode_conversion_rows(
            rows, [name for name, _type in columns]
        )

    return ResultsAggregates(
        specs=list(specs),
        exposure_counts=exposure_counts,
        metric_stats=metric_stats,
        granularity=granularity,
        exposure_buckets=get_exposure_buckets(
            environment_key=environment_key,
            feature_name=feature_name,
            window_start=window_start,
            window_end=window_end,
            granularity=granularity,
        ),
        conversion_buckets=conversion_buckets,
    )


def build_results_summary(
    aggregates: ResultsAggregates,
    *,
    expected_shares: dict[str, float],
) -> ResultsSummary:
    exposure_counts = aggregates.exposure_counts
    total = sum(exposure_counts.values())
    if expected_shares and total >= SRM_MIN_TOTAL_IDENTITIES:
        srm = srm_p_value(
            [exposure_counts.get(variant, 0) for variant in expected_shares],
            list(expected_shares.values()),
        )
    else:
        srm = None
    return ResultsSummary(
        srm_p_value=srm,
        metrics=[
            MetricResult(
                metric_id=spec.metric_id,
                variants=aggregates.metric_stats.get(spec.metric_id, {}),
                inference=_metric_inference(
                    spec, aggregates.metric_stats.get(spec.metric_id, {})
                ),
                conversions_timeseries=_conversions_timeseries(
                    spec.metric_id, aggregates
                ),
            )
            for spec in aggregates.specs
        ],
        exposures_timeseries=_exposures_timeseries(
            aggregates.exposure_buckets, granularity=aggregates.granularity
        ),
    )


def compute_results_summary(
    experiment: "Experiment",
    *,
    window_start: "datetime",
    window_end: "datetime",
) -> ResultsSummary:
    """Gather an experiment's metric statistics and chart rows from the
    warehouse and reduce them to the stored results payload."""
    aggregates = get_results_aggregates(
        environment_key=experiment.environment.api_key,
        feature_name=experiment.feature.name,
        window_start=window_start,
        window_end=window_end,
        specs=_experiment_metric_specs(experiment),
        granularity=_select_exposure_granularity(window_start, window_end),
    )
    return build_results_summary(
        aggregates,
        expected_shares=_expected_variant_shares(experiment),
    )


def _experiment_metric_specs(experiment: "Experiment") -> list[MetricSpec]:
    return [
        MetricSpec(
            metric_id=experiment_metric.metric_id,
            event=experiment_metric.metric.definition["event"],
            aggregation=experiment_metric.metric.aggregation,
            lower_is_better=(
                experiment_metric.metric.direction == MetricDirection.DOWN
            ),
        )
        for experiment_metric in experiment.experiment_metrics.select_related("metric")
    ]


def _expected_variant_shares(experiment: "Experiment") -> dict[str, float]:
    """The traffic split SRM tests against: each multivariate option's
    environment allocation, with ``control`` taking the unallocated remainder.
    Empty when the feature has no usable allocations, skipping the SRM check."""
    # TODO: read the split from the percentage-split segment override feature
    # state once that's implemented, rather than the environment default.
    feature_state = (
        FeatureState.objects.get_live_feature_states(
            environment=experiment.environment,
            additional_filters=Q(feature_segment__isnull=True, identity__isnull=True),
            feature_id=experiment.feature_id,
        )
        .prefetch_related(
            "multivariate_feature_state_values__multivariate_feature_option"
        )
        # Highest id is the current version, matching how Environment selects
        # active feature states (Max("id")); the default ordering is ascending.
        .order_by("-id")
        .first()
    )
    if feature_state is None:
        return {}

    shares: dict[str, float] = {}
    allocated = 0.0
    for mv_value in feature_state.multivariate_feature_state_values.all():
        key = mv_value.multivariate_feature_option.key
        if key is None:
            # An unkeyed option's traffic can't be attributed to a variant;
            # counting it as control would inflate control's expected share and
            # raise a false SRM alarm, so skip the check entirely.
            logger.error(
                "srm.unkeyed_variant",
                experiment__id=experiment.id,
                environment__id=experiment.environment_id,
                feature__id=experiment.feature_id,
            )
            return {}
        shares[key] = mv_value.percentage_allocation / 100
        allocated += mv_value.percentage_allocation
    if not shares:
        return {}
    if allocated > 100:
        # A misconfigured feature whose options over-allocate; control's share
        # would be negative, so there's no valid split to test against.
        logger.error(
            "srm.overallocated",
            experiment__id=experiment.id,
            environment__id=experiment.environment_id,
            feature__id=experiment.feature_id,
        )
        return {}
    shares[CONTROL_VARIANT_KEY] = (100 - allocated) / 100
    return shares


def _metric_inference(
    spec: MetricSpec,
    variants: dict[str, VariantStats],
) -> dict[str, Inference | None]:
    control = variants.get(CONTROL_VARIANT_KEY)
    return {
        variant_key: _infer_treatment(spec, control, treatment)
        for variant_key, treatment in variants.items()
        if variant_key != CONTROL_VARIANT_KEY
    }


def _infer_treatment(
    spec: MetricSpec,
    control: VariantStats | None,
    treatment: VariantStats,
) -> Inference | None:
    # Product floor for showing a result at all; compare_to_control applies its
    # own independent guards (e.g. zero control mean) on top of this.
    if (
        control is None
        or control.n < RESULTS_MIN_IDENTITIES_PER_VARIANT
        or treatment.n < RESULTS_MIN_IDENTITIES_PER_VARIANT
    ):
        return None
    if spec.aggregation == MetricAggregation.OCCURRENCE and (
        control.sum < RESULTS_MIN_CONVERSIONS_PER_VARIANT
        or treatment.sum < RESULTS_MIN_CONVERSIONS_PER_VARIANT
    ):
        return None
    inference = compare_to_control(control, treatment)
    if inference is not None and spec.lower_is_better:
        # "Winning" means moving the metric the good way; for a lower-is-better
        # metric that's a fall, so the chance of winning is the chance lift < 0.
        inference = replace(inference, chance_to_win=1.0 - inference.chance_to_win)
    return inference


def _resolve_audit_log_author(
    user: FFAdminUser,
) -> dict[str, int | None]:
    if getattr(user, "is_master_api_key_user", False):
        return {"author_id": None, "master_api_key_id": user.key.id}
    return {"author_id": user.pk, "master_api_key_id": None}


def create_warehouse_audit_log(
    connection: WarehouseConnection,
    user: FFAdminUser,
    *,
    action: str,
) -> None:
    AuditLog.objects.create(
        environment=connection.environment,
        project=connection.environment.project,
        **_resolve_audit_log_author(user),
        related_object_id=connection.id,
        related_object_type=RelatedObjectType.WAREHOUSE_CONNECTION.name,
        log=(
            f"Warehouse connection {action} for environment "
            f"{connection.environment.name}"
        ),
    )


def create_metric_audit_log(
    metric: Metric,
    user: FFAdminUser,
    *,
    action: str,
) -> None:
    AuditLog.objects.create(
        environment=metric.environment,
        project=metric.environment.project,
        **_resolve_audit_log_author(user),
        related_object_id=metric.id,
        related_object_type=RelatedObjectType.METRIC.name,
        log=f"Metric '{metric.name}' {action}",
    )


def create_experiment_audit_log(
    experiment: Experiment,
    user: FFAdminUser,
    *,
    action: str,
) -> None:
    AuditLog.objects.create(
        environment=experiment.environment,
        project=experiment.environment.project,
        **_resolve_audit_log_author(user),
        related_object_id=experiment.id,
        related_object_type=RelatedObjectType.EXPERIMENT.name,
        log=(
            f"Experiment '{experiment.name}' {action} for environment "
            f"{experiment.environment.name}"
        ),
    )


def _resolve_audit_log_author_data(author: AuthorData) -> dict[str, int | str | None]:
    if author.api_key is not None:
        return {"author_id": None, "master_api_key_id": author.api_key.id}
    return {
        "author_id": author.user.pk if author.user else None,
        "master_api_key_id": None,
    }


def create_rollout_audit_log(
    experiment: Experiment,
    author: AuthorData,
    *,
    rollout_percentage: float,
    audience_match: str,
    audience_segment_ids: list[int],
) -> None:
    audience = (
        f"segments {audience_segment_ids} ({audience_match})"
        if audience_segment_ids
        else "all identities"
    )
    AuditLog.objects.create(
        environment=experiment.environment,
        project=experiment.environment.project,
        **_resolve_audit_log_author_data(author),
        related_object_id=experiment.id,
        related_object_type=RelatedObjectType.EXPERIMENT.name,
        log=(
            f"Experiment '{experiment.name}' rollout set to "
            f"{rollout_percentage}% of {audience}"
        ),
    )


def transition_experiment_status(
    experiment: Experiment,
    target_status: str,
    user: FFAdminUser,
) -> Experiment:
    valid_targets = VALID_STATUS_TRANSITIONS.get(experiment.status, set())
    if target_status not in valid_targets:
        raise ValueError(
            f"Cannot transition from '{experiment.status}' to '{target_status}'."
        )

    experiment.status = target_status

    if target_status == ExperimentStatus.RUNNING and not experiment.started_at:
        experiment.started_at = timezone.now()
    elif target_status == ExperimentStatus.COMPLETED:
        experiment.ended_at = timezone.now()

    experiment.save()
    create_experiment_audit_log(experiment, user, action=target_status)
    return experiment


def _copy_segment_rule(rule: SegmentRule) -> SegmentRuleType:
    return {
        "type": typing.cast("RuleType", rule.type),
        "conditions": [
            {
                "property": condition.property,
                "operator": typing.cast("ConditionOperator", condition.operator),
                "value": condition.value,
                "description": condition.description,
            }
            for condition in rule.conditions.all()
        ],
        "rules": [_copy_segment_rule(sub_rule) for sub_rule in rule.rules.all()],
    }


def _copy_segment_rules(segment: Segment) -> list[SegmentRuleType]:
    """Snapshot a segment's rule tree. Read from the ORM rows rather than
    ``rules_data``: they are the evaluated representation, and the only one
    cohort segments have."""
    return [_copy_segment_rule(rule) for rule in segment.rules.all()]


def _compile_audience(
    experiment: Experiment,
    audience: AudienceSpec,
) -> tuple[list[SegmentRuleType], AudienceSnapshot]:
    """Validate, freeze and describe the audience in one pass: each segment is
    read once, then checked, compiled and snapshot from that same read, so a
    concurrent edit cannot slip rules past validation into the frozen copy."""
    segments = _get_audience_segments(experiment, audience.segment_ids)
    # Locked because cohort deletion locks the same rows before it scans for
    # experiments targeting them: without this a rollout could read a cohort as
    # live and commit after a concurrent deletion decided nothing targeted it.
    cohorts_by_segment_id = {
        cohort.segment_id: cohort
        for cohort in Cohort.objects.select_for_update()
        .filter(segment__in=segments)
        # A stable lock order, so two rollouts targeting overlapping cohorts
        # cannot deadlock each other.
        .order_by("pk")
    }
    copied_rules: list[list[SegmentRuleType]] = []
    snapshot_segments: list[AudienceSegmentSnapshot] = []
    for segment in segments:
        rules = _copy_segment_rules(segment)
        cohort = cohorts_by_segment_id.get(segment.id)
        _validate_audience_segment(experiment, segment, rules, cohort)
        copied_rules.append(rules)
        snapshot_segments.append(
            {
                "id": segment.id,
                "uuid": str(segment.uuid),
                "name": segment.name,
                "is_cohort": cohort is not None,
                "cohort_source_type": cohort.source_type if cohort else None,
            }
        )
    # An empty audience targets every identity, so there is no rule to add.
    compiled: list[SegmentRuleType] = (
        [
            {
                "type": ALL_RULE if audience.match == AudienceMatch.ALL else ANY_RULE,
                "conditions": [],
                # A segment's own top-level rules are AND-quantified, so a
                # multi-rule segment needs its own ALL wrapper. A single rule is
                # inlined: the shallower tree keeps the whole audience within
                # the document builder's prefetch depth and the org exporter's
                # two-level rule selection.
                "rules": [
                    (
                        rules[0]
                        if len(rules) == 1
                        else {"type": ALL_RULE, "conditions": [], "rules": rules}
                    )
                    for rules in copied_rules
                ],
            }
        ]
        if copied_rules
        else []
    )
    return compiled, {
        "match": audience.match,
        "segments": snapshot_segments,
        "rules": compiled,
        "taken_at": timezone.now().isoformat(),
    }


def _rollout_segment_rules(
    rollout_percentage: float,
    audience_rules: list[SegmentRuleType],
) -> list[SegmentRuleType]:
    """The rollout segment's rule tree: the percentage split, ANDed with the
    audience rule when there is one."""
    return [
        {
            "type": ALL_RULE,
            "conditions": [
                {
                    "property": "$.identity.key",
                    "operator": PERCENTAGE_SPLIT,
                    "value": str(rollout_percentage),
                    "description": None,
                }
            ],
            "rules": [],
        },
        *audience_rules,
    ]


def _write_segment_rule(
    rule: SegmentRuleType,
    *,
    segment: Segment | None = None,
    parent: SegmentRule | None = None,
) -> None:
    # TODO: Delete as per https://github.com/Flagsmith/flagsmith/issues/7818
    written = SegmentRule.objects.create(
        segment=segment, rule=parent, type=rule["type"]
    )
    for condition in rule["conditions"]:
        Condition.objects.create(
            rule=written,
            operator=condition["operator"],
            property=condition["property"],
            value=condition["value"],
            description=condition["description"],
        )
    for sub_rule in rule.get("rules", []):
        _write_segment_rule(sub_rule, parent=written)


def _write_segment_rules(segment: Segment, rules: list[SegmentRuleType]) -> None:
    """Rebuild the segment's legacy rule rows from the compiled tree. Nothing
    hashes on rule ids, so replacing them wholesale keeps every identity's
    enrolment and variant stable."""
    # TODO: Delete as per https://github.com/Flagsmith/flagsmith/issues/7818
    SegmentRule.objects.filter(segment=segment).delete()
    for rule in rules:
        _write_segment_rule(rule, segment=segment)


def _audience_match(experiment: Experiment) -> str:
    return experiment.audience.get("match", AudienceMatch.ANY.value)


def _audience_snapshot_segments(
    experiment: Experiment,
) -> list[AudienceSegmentSnapshot]:
    return experiment.audience.get("segments", [])


def _audience_changed(experiment: Experiment, audience: AudienceSpec) -> bool:
    stored_ids = sorted(
        segment["id"] for segment in _audience_snapshot_segments(experiment)
    )
    requested_ids = sorted(audience.segment_ids)
    if not stored_ids and not requested_ids:
        # With no segments on either side the combinator has nothing to
        # combine, so both describe the same "everyone" whatever the match.
        return False
    return requested_ids != stored_ids or audience.match != _audience_match(experiment)


def _audience_snapshots_equal(a: AudienceSnapshot, b: AudienceSnapshot) -> bool:
    """Whether two snapshots describe the same audience. `taken_at` only says
    when the copy was made, so it never makes two otherwise identical
    snapshots different."""
    return {key: value for key, value in a.items() if key != "taken_at"} == {
        key: value for key, value in b.items() if key != "taken_at"
    }


def _get_audience_segments(
    experiment: Experiment,
    segment_ids: list[int],
) -> list[Segment]:
    segments = list(
        Segment.live_objects.filter(
            project_id=experiment.feature.project_id, id__in=segment_ids
        ).order_by("id")
    )
    if missing := set(segment_ids) - {segment.id for segment in segments}:
        raise ValidationError(
            f"Audience segments {sorted(missing)} do not belong to the project"
        )
    return segments


def _rules_contain_percentage_split(rules: list[SegmentRuleType]) -> bool:
    return any(
        any(
            condition["operator"] == PERCENTAGE_SPLIT
            for condition in rule["conditions"]
        )
        or _rules_contain_percentage_split(rule.get("rules", []))
        for rule in rules
    )


def _validate_audience_segment(
    experiment: Experiment,
    segment: Segment,
    rules: list[SegmentRuleType],
    cohort: Cohort | None,
) -> None:
    if segment.is_system_segment:
        raise ValidationError(f"Audience segment {segment.id} cannot be targeted")
    if segment.feature_id is not None:
        raise ValidationError(f"Audience segment {segment.id} is specific to a feature")
    if cohort is not None:
        if cohort.environment_id != experiment.environment_id:
            raise ValidationError(
                f"Audience segment {segment.id} belongs to a cohort in another "
                f"environment"
            )
        if cohort.deletion_requested_at is not None:
            # Its memberships are draining, so the audience would decay to zero.
            raise ValidationError(
                f"Audience segment {segment.id} belongs to a cohort that is being "
                f"deleted"
            )
    if not rules:
        # An empty tree compiles to a rule that matches everyone, which would
        # silently widen the audience instead of narrowing it.
        raise ValidationError(f"Audience segment {segment.id} has no rules")
    if _rules_contain_percentage_split(rules):
        raise ValidationError(
            f"Audience segment {segment.id} contains a percentage split"
        )


def _rollout_override_enabled(experiment: Experiment) -> bool:
    return experiment.rollout_segment_id is not None and bool(
        (override := _get_live_rollout_override(experiment)) and override.enabled
    )


def _validate_audience_change(experiment: Experiment, audience: AudienceSpec) -> None:
    """Checks that only apply when the audience is actually being replaced. The
    caller has already established that it differs from the stored one."""
    if experiment.status != ExperimentStatus.CREATED:
        raise ValidationError(
            f"Cannot change the audience of a {experiment.status} experiment."
        )
    if _rollout_override_enabled(experiment):
        # An enabled override is already enrolling identities, whatever the
        # experiment's status says, and they were enrolled by these rules.
        raise ValidationError(
            "Cannot change the audience while the rollout is enabled and "
            "serving traffic. Disable the rollout first."
        )
    if len(audience.segment_ids) != len(set(audience.segment_ids)):
        raise ValidationError("Audience segments must be unique")
    if len(audience.segment_ids) > MAX_AUDIENCE_SEGMENTS:
        raise ValidationError(
            f"An audience must target no more than {MAX_AUDIENCE_SEGMENTS} segments"
        )


def validate_rollout_spec(experiment: Experiment, spec: RolloutSpec) -> None:
    option_ids = [v.multivariate_feature_option_id for v in spec.multivariate_values]
    if len(option_ids) != len(set(option_ids)):
        raise ValidationError("Multivariate options must be unique")
    valid_option_ids = set(
        experiment.feature.multivariate_options.values_list("id", flat=True)
    )
    if invalid := set(option_ids) - valid_option_ids:
        raise ValidationError(
            f"Multivariate options {sorted(invalid)} do not belong to the feature"
        )
    total = sum(v.percentage_allocation for v in spec.multivariate_values)
    if total > 100:
        raise ValidationError(
            f"Multivariate allocations must not exceed 100%, got {total}%."
        )


def _legacy_audience_rules(experiment: Experiment) -> list[SegmentRuleType]:
    """The audience rules of an experiment configured before the snapshot
    carried them, read back off the rollout segment: the percentage split is
    always its first rule."""
    segment = experiment.rollout_segment
    if segment is None or not (rules := segment.rules_data):
        return []
    return rules[1:]


def _frozen_audience_rules(experiment: Experiment) -> list[SegmentRuleType]:
    """The compiled audience rules to rebuild the rollout segment from. The
    snapshot is authoritative once it carries them, so a rollout segment that
    has since drifted is repaired rather than read back."""
    if (rules := experiment.audience.get("rules")) is not None:
        return rules
    return _legacy_audience_rules(experiment)


def _canonical_audience(experiment: Experiment) -> AudienceSnapshot:
    """The stored snapshot in canonical form. An experiment configured before
    the snapshot carried its compiled rules has them recovered from the rollout
    segment; a rollout with no audience gets an explicit empty snapshot rather
    than staying ``{}``. Either way the next sync reads the snapshot and not
    the segment."""
    snapshot = experiment.audience
    if "rules" in snapshot:
        return snapshot
    return {
        "match": _audience_match(experiment),
        "segments": _audience_snapshot_segments(experiment),
        "rules": _legacy_audience_rules(experiment),
        "taken_at": timezone.now().isoformat(),
    }


def _resolve_audience(
    experiment: Experiment,
    audience: AudienceSpec | None,
) -> tuple[list[SegmentRuleType], AudienceSnapshot]:
    """The rules to compile into the rollout segment and the snapshot describing
    them. Copies the audience segments when the audience is being set, and
    reuses the existing copy and snapshot otherwise, so that later edits to a
    source segment never drift a running experiment.

    Freezing only starts with enrolment: until the experiment leaves CREATED and
    the override serves traffic, a named audience is recompiled even when it
    matches the stored one, so pre-start edits to a source segment are picked
    up. Once frozen, an unchanged audience is never recompiled or revalidated:
    its rules already feed evaluation, and the source segments may since have
    been deleted or edited into something we would refuse to copy today."""
    if audience is None:
        return _frozen_audience_rules(experiment), _canonical_audience(experiment)
    if _audience_changed(experiment, audience):
        _validate_audience_change(experiment, audience)
        return _compile_audience(experiment, audience)
    if experiment.status == ExperimentStatus.CREATED and not (
        _rollout_override_enabled(experiment)
    ):
        return _compile_audience(experiment, audience)
    return _frozen_audience_rules(experiment), _canonical_audience(experiment)


def _store_audience(experiment: Experiment, snapshot: AudienceSnapshot) -> None:
    experiment.audience = snapshot
    experiment.save()


def _is_noop_rollout(
    experiment: Experiment,
    spec: RolloutSpec,
    rules: list[SegmentRuleType],
) -> bool:
    """True when the request asks for exactly what is already live. Such a
    request still succeeds, but writes no audit history and announces nothing:
    a re-submitted form is not a rollout change."""
    segment = experiment.rollout_segment
    if segment is None or segment.rules_data != rules:
        return False
    override = _get_live_rollout_override(experiment)
    if override is None or override.enabled != spec.enabled:
        return False
    if _serialize_feature_state_value(override.feature_state_value) != (
        spec.feature_state_value,
        spec.value_type,
    ):
        return False
    return {
        mv.multivariate_feature_option_id: mv.percentage_allocation
        for mv in override.multivariate_feature_state_values.all()
    } == {
        mv.multivariate_feature_option_id: mv.percentage_allocation
        for mv in spec.multivariate_values
    }


def _create_rollout_segment(
    experiment: Experiment,
    rules: list[SegmentRuleType],
) -> Segment:
    segment: Segment = Segment.objects.create(
        name=f"experiment-{experiment.id}-rollout",
        project=experiment.feature.project,
        is_system_segment=True,
        rules_data=rules,
    )
    _write_segment_rules(segment, rules)
    return segment


def _sync_rollout_segment(
    experiment: Experiment,
    rules: list[SegmentRuleType],
) -> Segment:
    segment = experiment.rollout_segment
    if segment is not None:
        if segment.rules_data == rules:
            # Nothing to rewrite: a value- or enabled-only change must not
            # churn the rule rows.
            return segment
        segment.rules_data = rules
        segment.save(update_fields=["rules_data"])
        _write_segment_rules(segment, rules)
        return segment
    segment = _create_rollout_segment(experiment, rules)
    experiment.rollout_segment = segment
    experiment.save()
    return segment


def _get_live_rollout_override(experiment: Experiment) -> FeatureState | None:
    flags = get_environment_flags_list(
        environment=experiment.environment,
        additional_filters=Q(
            feature_id=experiment.feature_id,
            feature_segment__segment_id=experiment.rollout_segment_id,
            identity__isnull=True,
        ),
    )
    return flags[0] if flags else None


def _update_live_feature_state(
    feature_state: FeatureState, change_set: FlagChangeSet
) -> None:
    feature_state.enabled = change_set.enabled
    feature_state.save()
    feature_state.feature_state_value.set_value(
        change_set.feature_state_value, change_set.type_
    )
    feature_state.feature_state_value.save()
    update_multivariate_values(feature_state, change_set.multivariate_values)


def _update_rollout_in_place(experiment: Experiment, change_set: FlagChangeSet) -> None:
    """Write the rollout-segment override, keeping variant assignment stable.

    Under v2 versioning, ``update_flag`` clones the override into a fresh feature
    state on every call. Since the multivariate split is salted on the feature
    state id, that would re-randomise control/variant for already-enrolled
    identities on each rollout update. Once the override exists, mutate it in
    place instead (no version is published). Creating the override, and v1
    versioning, still go through ``update_flag``, which already reuses the
    feature state.

    This is a temporary solution until we find a permanent fix for the
    underlying salting issue: https://github.com/Flagsmith/flagsmith/issues/7913
    """
    if experiment.environment.use_v2_feature_versioning and (
        override := _get_live_rollout_override(experiment)
    ):
        _update_live_feature_state(override, change_set)
        return
    update_flag(experiment.environment, experiment.feature, change_set)


def _reset_default_allocations_to_control(
    experiment: Experiment, author: AuthorData
) -> None:
    """Zero every variant's allocation on the feature's environment-default
    feature state, leaving control (the unallocated remainder) at 100%.

    Run once, when the rollout segment is first created: identities outside the
    rollout cohort should all receive control while the experiment runs.
    """
    (default_state,) = get_environment_flags_list(
        environment=experiment.environment,
        additional_filters=Q(
            feature_id=experiment.feature_id,
            feature_segment__isnull=True,
            identity__isnull=True,
        ),
    )
    str_value, value_type = _serialize_feature_state_value(
        default_state.feature_state_value
    )
    update_flag(
        experiment.environment,
        experiment.feature,
        FlagChangeSet(
            author=author,
            enabled=default_state.enabled,
            feature_state_value=str_value,
            type_=value_type,
            multivariate_values=[
                MultivariateValueChangeSet(
                    multivariate_feature_option_id=option_id,
                    percentage_allocation=0,
                )
                for option_id in experiment.feature.multivariate_options.values_list(
                    "id", flat=True
                )
            ],
        ),
    )


def apply_experiment_rollout(experiment: Experiment, spec: RolloutSpec) -> None:
    environment_id = experiment.environment_id
    with transaction.atomic():
        experiment.refresh_from_db(from_queryset=Experiment.objects.select_for_update())
        if experiment.status == ExperimentStatus.COMPLETED:
            raise ValidationError(
                f"Cannot change the rollout of a {experiment.status} experiment."
            )
        # Validate under the lock, against the status we just read: a concurrent
        # start must not let an audience change through the frozen-once-running
        # check on the strength of a stale instance.
        validate_rollout_spec(experiment, spec)
        audience_rules, audience_snapshot = _resolve_audience(experiment, spec.audience)
        rollout_rules = _rollout_segment_rules(spec.rollout_percentage, audience_rules)
        if (
            _is_noop_rollout(experiment, spec, rollout_rules)
            # A retarget to segments compiling to identical rules is still a
            # change worth recording.
            and _audience_snapshots_equal(audience_snapshot, experiment.audience)
        ):
            return
        if not _audience_snapshots_equal(audience_snapshot, experiment.audience):
            _store_audience(experiment, audience_snapshot)
        is_first_rollout = experiment.rollout_segment_id is None
        segment = _sync_rollout_segment(experiment, rollout_rules)
        if is_first_rollout:
            _reset_default_allocations_to_control(experiment, spec.author)
        _update_rollout_in_place(
            experiment,
            FlagChangeSet(
                author=spec.author,
                enabled=spec.enabled,
                feature_state_value=spec.feature_state_value,
                type_=spec.value_type,
                segment_id=segment.id,
                multivariate_values=spec.multivariate_values,
            ),
        )
        # Segment condition changes don't trigger a rebuild on their own.
        transaction.on_commit(
            lambda: rebuild_environment_document.delay(
                kwargs={"environment_id": environment_id}
            )
        )
        audience_match = _audience_match(experiment)
        audience_segment_ids = [
            audience_segment["id"]
            for audience_segment in _audience_snapshot_segments(experiment)
        ]
        create_rollout_audit_log(
            experiment,
            spec.author,
            rollout_percentage=spec.rollout_percentage,
            audience_match=audience_match,
            audience_segment_ids=audience_segment_ids,
        )
        # Read the audience now, but only announce the rollout once it is
        # durable: experiment creation nests this call in an outer transaction
        # that can still roll back.
        transaction.on_commit(
            lambda: experimentation_logger.info(
                "rollout.applied",
                experiment__id=experiment.id,
                environment__id=environment_id,
                feature__id=experiment.feature_id,
                author__id=spec.author.user.pk if spec.author.user else None,
                author__api_key_id=(
                    spec.author.api_key.pk if spec.author.api_key else None
                ),
                rollout__percentage=spec.rollout_percentage,
                audience__match=audience_match,
                audience__segments_count=len(audience_segment_ids),
                audience__segment_ids=audience_segment_ids,
            )
        )


def _serialize_feature_state_value(
    value: FeatureStateValue,
) -> tuple[str, FeatureValueType]:
    """Render a stored feature state value as the (string, API type) pair that
    a `FlagChangeSet` expects."""
    if value.value is None:
        return "", "string"
    return (
        str(value.value).lower() if value.type == BOOLEAN else str(value.value),
        API_VALUE_TYPES.get(value.type or STRING, "string"),
    )


def get_experiment_rollout(experiment: Experiment) -> dict[str, typing.Any] | None:
    segment_id = experiment.rollout_segment_id
    if segment_id is None:
        return None

    feature_state = FeatureState.objects.get_live_feature_states(
        environment=experiment.environment,
        additional_filters=Q(
            feature_segment__segment_id=segment_id, identity__isnull=True
        ),
        feature_id=experiment.feature_id,
    ).latest("id")

    condition = Condition.objects.get(
        rule__segment_id=segment_id, operator=PERCENTAGE_SPLIT
    )
    str_value, value_type = _serialize_feature_state_value(
        feature_state.feature_state_value
    )
    return {
        "enabled": feature_state.enabled,
        "rollout_percentage": float(condition.value or 0),
        "feature_state_value": {"type": value_type, "value": str_value},
        "multivariate_feature_state_values": [
            {
                "multivariate_feature_option": mv.multivariate_feature_option_id,
                "percentage_allocation": mv.percentage_allocation,
            }
            for mv in feature_state.multivariate_feature_state_values.all()
        ],
        "audience": _get_experiment_audience(experiment),
    }


def _get_experiment_audience(experiment: Experiment) -> dict[str, typing.Any]:
    """The stored snapshot, plus each segment's live deletion state. Names and
    cohort badges come from the snapshot, so they keep describing the audience
    the experiment launched with even once the source segment is gone."""
    segments = _audience_snapshot_segments(experiment)
    live_segment_ids = set(
        Segment.live_objects.filter(
            id__in=[segment["id"] for segment in segments]
        ).values_list("id", flat=True)
    )
    # Projected field by field rather than spread: the snapshot also carries
    # the compiled rules and provenance, which are ours and not the API's.
    return {
        "match": _audience_match(experiment),
        "segments": [
            {
                "id": segment["id"],
                "name": segment["name"],
                "is_cohort": segment["is_cohort"],
                "cohort_source_type": segment["cohort_source_type"],
                "deleted": segment["id"] not in live_segment_ids,
            }
            for segment in segments
        ],
    }


def enable_experiment_rollout(experiment: Experiment, author: AuthorData) -> None:
    rollout = get_experiment_rollout(experiment)
    if rollout is None or rollout["enabled"]:
        return

    value = rollout["feature_state_value"]
    _update_rollout_in_place(
        experiment,
        FlagChangeSet(
            author=author,
            enabled=True,
            feature_state_value=value["value"],
            type_=value["type"],
            segment_id=experiment.rollout_segment_id,
        ),
    )


def mark_warehouse_pending_connection(
    connection: WarehouseConnection,
) -> WarehouseConnection:
    """Move a connection from created to pending_connection. No-op for any
    other status."""
    if connection.status != WarehouseConnectionStatus.CREATED:
        return connection

    connection.status = WarehouseConnectionStatus.PENDING_CONNECTION
    connection.save(update_fields=["status"])
    logger.info(
        "connection.test_event_sent",
        environment__id=connection.environment_id,
        organisation__id=connection.environment.project.organisation_id,
    )
    return connection


def mark_warehouse_delivery_failed(
    connection: WarehouseConnection,
    detail: str,
) -> None:
    connection.status = WarehouseConnectionStatus.ERRORED
    connection.status_detail = detail[:255]
    connection.save(update_fields=["status", "status_detail"])


def mark_warehouse_delivery_succeeded(connection: WarehouseConnection) -> None:
    if connection.status == WarehouseConnectionStatus.CONNECTED:
        return

    connection.status = WarehouseConnectionStatus.CONNECTED
    connection.status_detail = None
    connection.save(update_fields=["status", "status_detail"])


def _deliver_pending_objects(
    client: ClickHouseHTTPClient,
    *,
    bucket_name: str,
    pending: list[str],
    connection: WarehouseConnection,
) -> tuple[int, int, int]:
    log = logger.bind(
        connection__id=connection.id,
        environment__id=connection.environment_id,
        organisation__id=connection.environment.project.organisation_id,
    )
    # A run that outlives the task timeout is retried while its own thread
    # keeps delivering, so it must finish first: whatever is left is picked up
    # on the next tick.
    deadline = time.monotonic() + DELIVERY_TIME_BUDGET_SECONDS
    delivered_count = rejected_count = rows_count = 0
    for index, s3_key in enumerate(pending):
        if time.monotonic() > deadline:
            log.info(
                "delivery.budget_exhausted",
                objects__remaining_count=len(pending) - index,
            )
            break
        try:
            object_rows_count = warehouse_delivery_service.deliver_object(
                client,
                bucket_name,
                s3_key,
            )
        except warehouse_delivery_service.ObjectRejectedError as exc:
            # This object's contents are the problem; the ones behind it are
            # still deliverable.
            warehouse_delivery_service.move_object(
                bucket_name,
                s3_key,
                to_prefix=warehouse_delivery_service.FAILED_PREFIX,
            )
            WarehouseDeliveryLog.objects.create(
                connection=connection,
                s3_key=s3_key,
                outcome=WarehouseDeliveryOutcome.REJECTED,
                error=str(exc),
            )
            rejected_count += 1
            flagsmith_experimentation_warehouse_delivery_objects_total.labels(
                result="rejected"
            ).inc()
            log.error(
                "delivery.object_rejected",
                s3__key=s3_key,
                exc_info=True,
            )
            continue
        warehouse_delivery_service.move_object(
            bucket_name,
            s3_key,
            to_prefix=warehouse_delivery_service.ARCHIVE_PREFIX,
        )
        WarehouseDeliveryLog.objects.create(
            connection=connection,
            s3_key=s3_key,
            outcome=WarehouseDeliveryOutcome.DELIVERED,
            rows_count=object_rows_count,
        )
        rows_count += object_rows_count
        delivered_count += 1
        flagsmith_experimentation_warehouse_delivery_objects_total.labels(
            result="delivered"
        ).inc()
    return delivered_count, rejected_count, rows_count


def deliver_warehouse_events(
    connection: WarehouseConnection,
    *,
    bucket_name: str,
) -> None:
    """Deliver the environment's pending event objects to the connection's
    warehouse, surfacing the outcome on the connection's status."""
    log = logger.bind(
        connection__id=connection.id,
        environment__id=connection.environment_id,
        organisation__id=connection.environment.project.organisation_id,
    )
    pending = warehouse_delivery_service.list_pending_objects(
        bucket_name,
        environment_key=connection.environment.api_key,
    )
    if not pending:
        return

    try:
        with warehouse_delivery_service.delivery_client(connection) as client:
            delivered_count, rejected_count, rows_count = _deliver_pending_objects(
                client,
                bucket_name=bucket_name,
                pending=pending,
                connection=connection,
            )
    except (warehouse_delivery_service.DeliveryConfigError, ClickHouseError) as exc:
        # The warehouse itself is unusable; deliver nothing, leave every
        # remaining object in place for the next run, and surface the
        # breakage on the connection. Anything else — an S3 failure, a bug
        # here — is ours, so it propagates and fails the task instead of
        # blaming the customer's warehouse.
        mark_warehouse_delivery_failed(
            connection,
            detail=warehouse_delivery_service.describe_warehouse_error(exc),
        )
        flagsmith_experimentation_warehouse_delivery_runs_total.labels(
            result="failure"
        ).inc()
        log.error("delivery.failed", exc_info=exc)
        return

    if delivered_count == 0 and rejected_count:
        # Records all come from one ingestion pipeline, so every object being
        # rejected points at the table's schema rather than the objects.
        mark_warehouse_delivery_failed(
            connection,
            detail=(
                f"The warehouse rejected every event object. Check that the "
                f"`{warehouse_delivery_service.EVENTS_TABLE_NAME}` table "
                f"matches the expected schema."
            ),
        )
        flagsmith_experimentation_warehouse_delivery_runs_total.labels(
            result="failure"
        ).inc()
        log.error(
            "delivery.all_objects_rejected",
            objects__rejected_count=rejected_count,
        )
        return

    mark_warehouse_delivery_succeeded(connection)
    flagsmith_experimentation_warehouse_delivery_runs_total.labels(
        result="success"
    ).inc()
    log.info(
        "delivery.completed",
        objects__count=delivered_count,
        objects__rejected_count=rejected_count,
        rows__count=rows_count,
    )


def verify_clickhouse_connection(
    connection: WarehouseConnection,
    persist: bool = True,
) -> None:
    """Check the customer's events table exists, connecting over the same
    client, interface and port that delivery uses, and set the status to
    connected or errored; never raises. With persist=False, the status is only
    set on the in-memory instance, allowing unsaved connections to be
    tested."""
    log = logger.bind(environment__id=connection.environment_id)
    try:
        log = log.bind(organisation__id=connection.environment.project.organisation_id)
        with warehouse_delivery_service.delivery_client(
            connection,
            send_receive_timeout=CLICKHOUSE_VERIFY_TIMEOUT_SECONDS,
        ) as client:
            warehouse_delivery_service.check_events_table_exists(client)
    except Exception as error:
        connection.status = WarehouseConnectionStatus.ERRORED
        connection.status_detail = warehouse_delivery_service.describe_warehouse_error(
            error
        )
        if persist:
            connection.save(update_fields=["status", "status_detail"])
        flagsmith_experimentation_warehouse_connection_verifications_total.labels(
            result="failure"
        ).inc()
        log.warning("connection.verification_failed", exc_info=True)
        return

    connection.status = WarehouseConnectionStatus.CONNECTED
    connection.status_detail = None
    if persist:
        connection.save(update_fields=["status", "status_detail"])
    flagsmith_experimentation_warehouse_connection_verifications_total.labels(
        result="success"
    ).inc()
    log.info("connection.verification_succeeded")


def refresh_warehouse_connection_status(
    connection: WarehouseConnection,
    stats: WarehouseEventStats,
) -> WarehouseConnection:
    """Set a pending connection to connected when the warehouse has received at
    least one event. No-op otherwise."""
    if (
        connection.status == WarehouseConnectionStatus.PENDING_CONNECTION
        and stats.total_events_received > 0
    ):
        connection.status = WarehouseConnectionStatus.CONNECTED
        connection.save(update_fields=["status"])
        logger.info(
            "connection.connected",
            environment__id=connection.environment_id,
            organisation__id=connection.environment.project.organisation_id,
        )
    return connection


def annotate_warehouse_event_stats(
    connection: WarehouseConnection,
    environment_key: str,
) -> None:
    """Attach live warehouse event stats to a connection — from the managed
    warehouse for flagsmith connections, from the customer's instance for
    clickhouse ones. No-op for other types or when no warehouse is configured;
    leaves stats unset when the warehouse is unreachable. Read-only: never
    changes status."""
    if connection.warehouse_type == WarehouseType.CLICKHOUSE:
        stats = _get_customer_warehouse_event_stats_cached(connection, environment_key)
        if stats is not None:
            connection.event_stats = stats
        return
    if (
        connection.warehouse_type != WarehouseType.FLAGSMITH
        or not settings.EXPERIMENTATION_CLICKHOUSE_URL
    ):
        return
    try:
        connection.event_stats = get_warehouse_event_stats(environment_key)
    except Exception:
        return


def _get_customer_warehouse_event_stats_cached(
    connection: WarehouseConnection,
    environment_key: str,
) -> WarehouseEventStats | None:
    """Return event counts recorded for `environment_key` in the customer's
    ClickHouse instance, or None when it's unreachable. Results — including
    failures — are cached briefly so read endpoints don't open a connection to
    the customer's host on every request."""
    cache_key = _customer_cache_key("event_stats", connection)
    cached = cache.get(cache_key)
    if isinstance(cached, WarehouseEventStats):
        return cached
    if cached == _CUSTOMER_EVENT_UNAVAILABLE:
        return None
    try:
        with warehouse_delivery_service.delivery_client(
            connection,
            send_receive_timeout=CLICKHOUSE_VERIFY_TIMEOUT_SECONDS,
        ) as client:
            rows = client.query(
                _EVENT_STATS_QUERY,
                parameters={"environment_key": environment_key},
            ).result_rows
        stats = _build_event_stats(rows)
    except Exception:
        cache.set(
            cache_key,
            _CUSTOMER_EVENT_UNAVAILABLE,
            CUSTOMER_EVENT_STATS_CACHE_SECONDS,
        )
        logger.warning(
            "connection.event_stats_failed",
            environment__id=connection.environment_id,
            exc_info=True,
        )
        return None
    cache.set(cache_key, stats, CUSTOMER_EVENT_STATS_CACHE_SECONDS)
    return stats


def _get_customer_clickhouse_event_names(
    connection: "WarehouseConnection",
    environment_key: str,
) -> WarehouseEventNames | None:
    """Query the customer's ClickHouse instance, caching results — including
    failures — to spare their host repeated connections."""
    cache_key = _customer_cache_key("event_names", connection)
    cached = cache.get(cache_key)
    if isinstance(cached, WarehouseEventNames):
        return cached
    if cached == _CUSTOMER_EVENT_UNAVAILABLE:
        return None
    try:
        with warehouse_delivery_service.delivery_client(
            connection,
            send_receive_timeout=CLICKHOUSE_EVENT_NAMES_TIMEOUT_SECONDS,
        ) as client:
            rows = client.query(
                _CLICKHOUSE_EVENT_NAMES_QUERY,
                parameters=_event_names_query_params(environment_key),
            ).result_rows
    except Exception:
        cache.set(
            cache_key,
            _CUSTOMER_EVENT_UNAVAILABLE,
            CUSTOMER_EVENT_NAMES_FAILURE_CACHE_SECONDS,
        )
        logger.warning(
            "connection.event_names_failed",
            environment__id=connection.environment_id,
            exc_info=True,
        )
        return None
    event_names = _build_event_names(rows)
    cache.set(cache_key, event_names, EVENT_NAMES_CACHE_SECONDS)
    return event_names
