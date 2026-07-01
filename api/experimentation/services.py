from __future__ import annotations

import typing
from dataclasses import replace
from functools import lru_cache

import structlog
from clickhouse_driver import Client
from clickhouse_driver.util.helpers import parse_url
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from flag_engine.segments.constants import PERCENTAGE_SPLIT
from rest_framework.exceptions import ValidationError

from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from core.dataclasses import AuthorData
from environments.tasks import rebuild_environment_document
from experimentation.constants import (
    CONTROL_VARIANT_KEY,
    EXPERIMENT_FLAG,
    EXPOSURE_EVENT_NAME,
    EXPOSURE_HOURLY_BUCKET_MAX_WINDOW,
    RESULTS_MIN_CONVERSIONS_PER_VARIANT,
    RESULTS_MIN_IDENTITIES_PER_VARIANT,
    SRM_MIN_TOTAL_IDENTITIES,
    WAREHOUSE_CONNECTION_FLAG,
)
from experimentation.dataclasses import (
    ExposureBucket,
    ExposuresSummary,
    ExposuresTimeseries,
    ExposuresTimeseriesPoint,
    MetricResult,
    MetricSpec,
    ResultsAggregates,
    ResultsSummary,
    RolloutSpec,
    WarehouseEventStats,
)
from experimentation.models import (
    VALID_STATUS_TRANSITIONS,
    ExperimentStatus,
    MetricAggregation,
    MetricDirection,
    WarehouseConnectionStatus,
    WarehouseType,
)
from experimentation.results_query import _EXPOSURES_CTE, ResultsQueryBuilder
from experimentation.stats import (
    Inference,
    VariantStats,
    compare_to_control,
    srm_p_value,
)
from features.models import FeatureState
from features.value_types import BOOLEAN, INTEGER, STRING
from features.versioning.dataclasses import FlagChangeSet
from features.versioning.versioning_service import (
    update_flag,
    update_multivariate_values,
)
from integrations.flagsmith.client import get_openfeature_client
from segments.models import Condition, Segment, SegmentRule

_ROLLOUT_VALUE_TYPE = {INTEGER: "integer", STRING: "string", BOOLEAN: "boolean"}

if typing.TYPE_CHECKING:
    from collections.abc import Sequence
    from datetime import datetime

    from experimentation.models import Experiment, Metric, WarehouseConnection
    from experimentation.types import ExposureGranularity
    from organisations.models import Organisation
    from users.models import FFAdminUser

logger = structlog.get_logger("warehouse")

CLICKHOUSE_CONNECT_TIMEOUT_SECONDS = 5
CLICKHOUSE_QUERY_TIMEOUT_SECONDS = 30


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


@lru_cache(maxsize=1)
def _get_clickhouse_client() -> Client:
    """Build a clickhouse-driver client for the experimentation event store.

    The database is taken from the DSN path, so queries can reference the
    `events` table unqualified. Connect and query timeouts are bounded unless the
    DSN overrides them.
    """
    host, kwargs = parse_url(settings.EXPERIMENTATION_CLICKHOUSE_URL)
    kwargs.setdefault("connect_timeout", CLICKHOUSE_CONNECT_TIMEOUT_SECONDS)
    kwargs.setdefault("send_receive_timeout", CLICKHOUSE_QUERY_TIMEOUT_SECONDS)
    return Client(host, **kwargs)


def get_unique_event_names(environment_key: str) -> list[str]:
    """Return the distinct event names recorded for `environment_key`,
    ordered alphabetically."""
    rows = _get_clickhouse_client().execute(
        "SELECT DISTINCT event FROM events "
        "WHERE environment_key = %(environment_key)s "
        "ORDER BY event",
        {"environment_key": environment_key},
    )
    return [row[0] for row in rows]


def get_warehouse_event_stats(environment_key: str) -> WarehouseEventStats:
    """Return event counts recorded for `environment_key` in the warehouse."""
    rows = _get_clickhouse_client().execute(
        "SELECT count() AS total, uniqExact(event) AS unique "
        "FROM events WHERE environment_key = %(environment_key)s",
        {"environment_key": environment_key},
    )
    total, unique = rows[0] if rows else (0, 0)
    return WarehouseEventStats(
        total_events_received=int(total),
        unique_events_count=int(unique),
    )


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
        timeseries=ExposuresTimeseries(
            granularity=granularity,
            points=_timeseries_points([b for b in buckets if not b.quarantined]),
        ),
    )


def _timeseries_points(
    buckets: Sequence[ExposureBucket],
) -> list[ExposuresTimeseriesPoint]:
    new_identities_by_bucket: dict[datetime, dict[str, int]] = {}
    for b in buckets:
        new_identities_by_bucket.setdefault(b.bucket, {})[b.variant] = (
            b.first_exposed_identities
        )
    return [
        ExposuresTimeseriesPoint(
            bucket=bucket_start.isoformat(),
            new_identities=new_identities_by_bucket[bucket_start],
        )
        for bucket_start in sorted(new_identities_by_bucket)
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
    rows = _get_clickhouse_client().execute(
        EXPOSURE_BUCKETS_QUERY.format(
            bucket_function=_EXPOSURE_BUCKET_FUNCTIONS[granularity]
        ),
        {
            "environment_key": environment_key,
            "exposure_event": EXPOSURE_EVENT_NAME,
            "feature_name": feature_name,
            "window_start": window_start,
            "window_end": window_end,
        },
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


def get_metric_variant_stats(
    *,
    environment_key: str,
    feature_name: str,
    window_start: datetime,
    window_end: datetime,
    specs: Sequence[MetricSpec],
) -> ResultsAggregates:
    """Run the warehouse query, returning per-variant identity counts and, per
    metric, per-variant sufficient statistics."""
    builder = ResultsQueryBuilder(specs)
    params: dict[str, object] = {
        "environment_key": environment_key,
        "exposure_event": EXPOSURE_EVENT_NAME,
        "feature_name": feature_name,
        "window_start": window_start,
        "window_end": window_end,
    }
    builder.add_metric_params(params)

    rows, columns = _get_clickhouse_client().execute(
        builder.build_query(), params, with_column_types=True
    )
    exposure_counts, metric_stats = builder.decode_rows(
        rows, [name for name, _type in columns]
    )

    return ResultsAggregates(
        specs=list(specs),
        exposure_counts=exposure_counts,
        metric_stats=metric_stats,
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
            )
            for spec in aggregates.specs
        ],
    )


def compute_results_summary(
    experiment: "Experiment",
    *,
    window_start: "datetime",
    window_end: "datetime",
) -> ResultsSummary:
    """Gather an experiment's metric statistics from the warehouse and reduce
    them to the stored results payload."""
    specs = _experiment_metric_specs(experiment)
    aggregates = get_metric_variant_stats(
        environment_key=experiment.environment.api_key,
        feature_name=experiment.feature.name,
        window_start=window_start,
        window_end=window_end,
        specs=specs,
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


def _create_rollout_segment(
    experiment: Experiment, rollout_percentage: float
) -> Segment:
    segment: Segment = Segment.objects.create(
        name=f"experiment-{experiment.id}-rollout",
        project=experiment.feature.project,
        is_system_segment=True,
    )
    rule = SegmentRule.objects.create(segment=segment, type=SegmentRule.ALL_RULE)
    Condition.objects.create(
        rule=rule,
        operator=PERCENTAGE_SPLIT,
        property="$.identity.key",
        value=str(rollout_percentage),
    )
    return segment


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


def _sync_rollout_segment(experiment: Experiment, rollout_percentage: float) -> Segment:
    segment = experiment.rollout_segment
    if segment is not None:
        condition = Condition.objects.get(
            rule__segment=segment, operator=PERCENTAGE_SPLIT
        )
        condition.value = str(rollout_percentage)
        condition.save()
        return segment
    segment = _create_rollout_segment(experiment, rollout_percentage)
    experiment.rollout_segment = segment
    experiment.save()
    return segment


def _get_live_rollout_override(experiment: Experiment) -> FeatureState | None:
    return (
        FeatureState.objects.get_live_feature_states(
            environment=experiment.environment,
            additional_filters=Q(
                feature_segment__segment_id=experiment.rollout_segment_id,
                identity__isnull=True,
            ),
            feature_id=experiment.feature_id,
        )
        .order_by("-id")
        .first()
    )


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


def apply_experiment_rollout(experiment: Experiment, spec: RolloutSpec) -> None:
    if experiment.status == ExperimentStatus.COMPLETED:
        raise ValidationError(
            f"Cannot change the rollout of a {experiment.status} experiment."
        )
    validate_rollout_spec(experiment, spec)
    environment_id = experiment.environment_id
    with transaction.atomic():
        segment = _sync_rollout_segment(experiment, spec.rollout_percentage)
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
    value = feature_state.feature_state_value
    return {
        "enabled": feature_state.enabled,
        "rollout_percentage": float(condition.value or 0),
        "feature_state_value": {
            "type": _ROLLOUT_VALUE_TYPE.get(value.type or STRING, "string"),
            "value": (
                str(value.value).lower() if value.type == BOOLEAN else str(value.value)
            ),
        },
        "multivariate_feature_state_values": [
            {
                "multivariate_feature_option": mv.multivariate_feature_option_id,
                "percentage_allocation": mv.percentage_allocation,
            }
            for mv in feature_state.multivariate_feature_state_values.all()
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
    """Attach live warehouse event stats to a flagsmith connection. No-op for
    non-flagsmith connections or when no warehouse is configured; leaves stats
    unset when the warehouse is unreachable. Read-only: never changes status."""
    if (
        connection.warehouse_type != WarehouseType.FLAGSMITH
        or not settings.EXPERIMENTATION_CLICKHOUSE_URL
    ):
        return
    try:
        connection.event_stats = get_warehouse_event_stats(environment_key)
    except Exception:
        return
