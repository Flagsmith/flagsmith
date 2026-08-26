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
from flag_engine.segments.constants import ALL_RULE, PERCENTAGE_SPLIT
from rest_framework.exceptions import ValidationError

from audit.models import AuditLog
from audit.related_object_type import RelatedObjectType
from core.dataclasses import AuthorData
from environments.tasks import rebuild_environment_document
from experimentation import warehouse_delivery_service
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
from experimentation.results_query import _EXPOSURES_CTE, ResultsQueryBuilder
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

    from environments.models import Environment
    from experimentation.models import Metric
    from experimentation.types import ExposureGranularity
    from features.feature_states.models import FeatureValueType
    from features.models import FeatureStateValue
    from organisations.models import Organisation
    from users.models import FFAdminUser

logger = structlog.get_logger("warehouse")

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
        return WarehouseConnection.objects.create(
            environment=environment,
            warehouse_type=WarehouseType.FLAGSMITH,
            name="Flagsmith",
        )
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
    rows = _get_clickhouse_client(
        send_receive_timeout=CLICKHOUSE_BACKGROUND_QUERY_TIMEOUT_SECONDS,
    ).execute(
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

    rows, columns = _get_clickhouse_client(
        send_receive_timeout=CLICKHOUSE_BACKGROUND_QUERY_TIMEOUT_SECONDS,
    ).execute(builder.build_query(), params, with_column_types=True)
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


def _rollout_segment_rules(rollout_percentage: float) -> list[SegmentRuleType]:
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
        }
    ]


def _create_rollout_segment(
    experiment: Experiment, rollout_percentage: float
) -> Segment:
    segment: Segment = Segment.objects.create(
        name=f"experiment-{experiment.id}-rollout",
        project=experiment.feature.project,
        is_system_segment=True,
        rules_data=_rollout_segment_rules(rollout_percentage),
    )

    # TODO: Delete as per https://github.com/Flagsmith/flagsmith/issues/7818
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
        segment.rules_data = _rollout_segment_rules(rollout_percentage)
        segment.save(update_fields=["rules_data"])

        # TODO: Delete as per https://github.com/Flagsmith/flagsmith/issues/7818
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
    validate_rollout_spec(experiment, spec)
    environment_id = experiment.environment_id
    with transaction.atomic():
        experiment.refresh_from_db(from_queryset=Experiment.objects.select_for_update())
        if experiment.status == ExperimentStatus.COMPLETED:
            raise ValidationError(
                f"Cannot change the rollout of a {experiment.status} experiment."
            )
        is_first_rollout = experiment.rollout_segment_id is None
        segment = _sync_rollout_segment(experiment, spec.rollout_percentage)
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
