from datetime import datetime, timedelta
from typing import List, Tuple

from django.conf import settings
from django.db.models import Q, Sum
from django.utils import timezone
from task_processor.decorators import (
    register_recurring_task,
    register_task_handler,
)

from app_analytics.constants import ANALYTICS_READ_BUCKET_SIZE
from app_analytics.models import (
    APIUsageBucket,
    APIUsageRaw,
    FeatureEvaluationBucket,
    FeatureEvaluationRaw,
    Resource,
)
from app_analytics.track import (
    track_feature_evaluation_influxdb as track_feature_evaluation_influxdb_service,
)
from app_analytics.track import (
    track_feature_evaluation_influxdb_v2 as track_feature_evaluation_influxdb_v2_service,
)
from app_analytics.track import (
    track_request_influxdb,
)
from environments.models import Environment

if settings.USE_POSTGRES_FOR_ANALYTICS:  # pragma: no cover

    @register_recurring_task(
        run_every=timedelta(minutes=60),
        kwargs={
            "bucket_size": ANALYTICS_READ_BUCKET_SIZE,
            "run_every": 60,
        },
    )
    def populate_bucket(  # type: ignore[no-untyped-def]
        bucket_size: int,
        run_every: int,
        source_bucket_size: int = None,  # type: ignore[assignment]
    ):
        populate_api_usage_bucket(bucket_size, run_every, source_bucket_size)
        populate_feature_evaluation_bucket(bucket_size, run_every, source_bucket_size)


@register_recurring_task(
    run_every=timedelta(days=1),
)
def clean_up_old_analytics_data():  # type: ignore[no-untyped-def]
    # delete raw analytics data older than `RAW_ANALYTICS_DATA_RETENTION_DAYS`
    APIUsageRaw.objects.filter(
        created_at__lt=timezone.now()
        - timedelta(days=settings.RAW_ANALYTICS_DATA_RETENTION_DAYS)
    ).delete()
    FeatureEvaluationRaw.objects.filter(
        created_at__lt=timezone.now()
        - timedelta(days=settings.RAW_ANALYTICS_DATA_RETENTION_DAYS)
    ).delete()

    # delete bucketed analytics data older than `BUCKETED_ANALYTICS_DATA_RETENTION_DAYS`
    APIUsageBucket.objects.filter(
        created_at__lt=timezone.now()
        - timedelta(days=settings.BUCKETED_ANALYTICS_DATA_RETENTION_DAYS)
    ).delete()

    FeatureEvaluationBucket.objects.filter(
        created_at__lt=timezone.now()
        - timedelta(days=settings.BUCKETED_ANALYTICS_DATA_RETENTION_DAYS)
    ).delete()


@register_task_handler()
def track_feature_evaluation_v2(
    environment_id: int, feature_evaluations: list[dict[str, int | str | bool]]
) -> None:
    feature_evaluation_objects = []
    for feature_evaluation in feature_evaluations:
        feature_evaluation_objects.append(
            FeatureEvaluationRaw(  # type: ignore[misc]
                environment_id=environment_id,
                feature_name=feature_evaluation["feature_name"],
                evaluation_count=feature_evaluation["count"],
                identity_identifier=feature_evaluation["identity_identifier"],
                enabled_when_evaluated=feature_evaluation["enabled_when_evaluated"],
            )
        )
    FeatureEvaluationRaw.objects.bulk_create(feature_evaluation_objects)


@register_task_handler()
def track_feature_evaluation(
    environment_id: int,
    feature_evaluations: dict[str, int],
) -> None:
    feature_evaluation_objects = []
    for feature_name, evaluation_count in feature_evaluations.items():
        feature_evaluation_objects.append(
            FeatureEvaluationRaw(
                feature_name=feature_name,
                environment_id=environment_id,
                evaluation_count=evaluation_count,
            )
        )
    FeatureEvaluationRaw.objects.bulk_create(feature_evaluation_objects)


@register_task_handler()
def track_request(
    resource: int,
    host: str,
    environment_key: str,
    count: int = 1,
) -> None:
    if environment := Environment.get_from_cache(environment_key):
        resource = Resource(resource)
        if settings.USE_POSTGRES_FOR_ANALYTICS:
            APIUsageRaw.objects.create(
                resource=resource,
                host=host,
                environment_id=environment.id,
                count=count,
            )
        elif settings.INFLUXDB_TOKEN:
            track_request_influxdb(
                resource=resource,
                host=host,
                environment=environment,
                count=count,
            )


track_feature_evaluation_influxdb = register_task_handler()(
    track_feature_evaluation_influxdb_service
)

track_feature_evaluation_influxdb_v2 = register_task_handler()(
    track_feature_evaluation_influxdb_v2_service
)


def get_start_of_current_bucket(bucket_size: int) -> datetime:
    if bucket_size > 60:
        raise ValueError("Bucket size cannot be greater than 60 minutes")

    current_time = timezone.now().replace(second=0, microsecond=0)
    start_of_current_bucket = current_time - timezone.timedelta(  # type: ignore[attr-defined]
        minutes=current_time.minute % bucket_size
    )
    return start_of_current_bucket  # type: ignore[no-any-return]


def get_time_buckets(
    bucket_size: int, run_every: int
) -> List[Tuple[datetime, datetime]]:
    start_of_first_bucket = get_start_of_current_bucket(bucket_size)
    time_buckets = []

    # number of buckets that can be processed in `run_every` time
    num_of_buckets = run_every // bucket_size
    for i in range(num_of_buckets):
        # NOTE: we start processing from `current - 1` buckets since the current bucket is
        # still open
        end_time = start_of_first_bucket - timezone.timedelta(minutes=bucket_size * i)  # type: ignore[attr-defined]
        start_time = end_time - timezone.timedelta(minutes=bucket_size)  # type: ignore[attr-defined]
        time_buckets.append((start_time, end_time))

    return time_buckets


def populate_api_usage_bucket(  # type: ignore[no-untyped-def]
    bucket_size: int,
    run_every: int,
    source_bucket_size: int = None,  # type: ignore[assignment]
):
    for bucket_start_time, bucket_end_time in get_time_buckets(bucket_size, run_every):
        data = _get_api_usage_source_data(
            bucket_start_time, bucket_end_time, source_bucket_size
        )
        for row in data:
            APIUsageBucket.objects.update_or_create(
                defaults={"total_count": row["count"]},
                environment_id=row["environment_id"],
                resource=row["resource"],
                bucket_size=bucket_size,
                created_at=bucket_start_time,
            )


def populate_feature_evaluation_bucket(  # type: ignore[no-untyped-def]
    bucket_size: int,
    run_every: int,
    source_bucket_size: int = None,  # type: ignore[assignment]
):
    for bucket_start_time, bucket_end_time in get_time_buckets(bucket_size, run_every):
        data = _get_feature_evaluation_source_data(
            bucket_start_time, bucket_end_time, source_bucket_size
        )
        for row in data:
            FeatureEvaluationBucket.objects.update_or_create(
                defaults={"total_count": row["count"]},
                environment_id=row["environment_id"],
                feature_name=row["feature_name"],
                bucket_size=bucket_size,
                created_at=bucket_start_time,
            )


def _get_api_usage_source_data(
    process_from: datetime,
    process_till: datetime,
    source_bucket_size: int = None,  # type: ignore[assignment]
) -> dict:  # type: ignore[type-arg]
    filters = Q(
        created_at__lte=process_till,
        created_at__gt=process_from,
    )
    if source_bucket_size:
        return (
            APIUsageBucket.objects.filter(filters, bucket_size=source_bucket_size)  # type: ignore[return-value]
            .values("environment_id", "resource")
            .annotate(count=Sum("total_count"))
        )
    return (
        APIUsageRaw.objects.filter(filters)  # type: ignore[return-value]
        .values("environment_id", "resource")
        .annotate(count=Sum("count"))
    )


def _get_feature_evaluation_source_data(
    process_from: datetime,
    process_till: datetime,
    source_bucket_size: int = None,  # type: ignore[assignment]
) -> dict:  # type: ignore[type-arg]
    filters = Q(
        created_at__lte=process_till,
        created_at__gt=process_from,
    )
    if source_bucket_size:
        return (
            FeatureEvaluationBucket.objects.filter(  # type: ignore[return-value]
                filters, bucket_size=source_bucket_size
            )
            .values("environment_id", "feature_name")
            .annotate(count=Sum("total_count"))
        )
    return (
        FeatureEvaluationRaw.objects.filter(filters)  # type: ignore[return-value]
        .values("environment_id", "feature_name")
        .annotate(count=Sum("evaluation_count"))
    )
