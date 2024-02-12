from datetime import datetime, timedelta
from typing import List, Tuple

from app_analytics.analytics_db_service import ANALYTICS_READ_BUCKET_SIZE
from django.conf import settings
from django.db.models import Count, Q, Sum
from django.utils import timezone

from environments.models import Environment
from task_processor.decorators import (
    register_recurring_task,
    register_task_handler,
)

from .models import (
    APIUsageBucket,
    APIUsageRaw,
    FeatureEvaluationBucket,
    FeatureEvaluationRaw,
)

if settings.USE_POSTGRES_FOR_ANALYTICS:

    @register_recurring_task(
        run_every=timedelta(minutes=60),
        kwargs={
            "bucket_size": ANALYTICS_READ_BUCKET_SIZE,
            "run_every": 60,
        },
    )
    def populate_bucket(
        bucket_size: int, run_every: int, source_bucket_size: int = None
    ):
        populate_api_usage_bucket(bucket_size, run_every, source_bucket_size)
        populate_feature_evaluation_bucket(bucket_size, run_every, source_bucket_size)


@register_recurring_task(
    run_every=timedelta(days=1),
)
def clean_up_old_analytics_data():
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
            FeatureEvaluationRaw(
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
def track_request(resource: int, host: str, environment_key: str):
    environment = Environment.get_from_cache(environment_key)
    if environment is None:
        return
    APIUsageRaw.objects.create(
        environment_id=environment.id,
        resource=resource,
        host=host,
    )


def get_start_of_current_bucket(bucket_size: int) -> datetime:
    if bucket_size > 60:
        raise ValueError("Bucket size cannot be greater than 60 minutes")

    current_time = timezone.now().replace(second=0, microsecond=0)
    start_of_current_bucket = current_time - timezone.timedelta(
        minutes=current_time.minute % bucket_size
    )
    return start_of_current_bucket


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
        end_time = start_of_first_bucket - timezone.timedelta(minutes=bucket_size * i)
        start_time = end_time - timezone.timedelta(minutes=bucket_size)
        time_buckets.append((start_time, end_time))

    return time_buckets


def populate_api_usage_bucket(
    bucket_size: int, run_every: int, source_bucket_size: int = None
):
    for bucket_start_time, bucket_end_time in get_time_buckets(bucket_size, run_every):
        data = _get_api_usage_source_data(
            bucket_start_time, bucket_end_time, source_bucket_size
        )
        for row in data:
            APIUsageBucket.objects.create(
                environment_id=row["environment_id"],
                resource=row["resource"],
                total_count=row["count"],
                bucket_size=bucket_size,
                created_at=bucket_start_time,
            )


def populate_feature_evaluation_bucket(
    bucket_size: int, run_every: int, source_bucket_size: int = None
):
    for bucket_start_time, bucket_end_time in get_time_buckets(bucket_size, run_every):
        data = _get_feature_evaluation_source_data(
            bucket_start_time, bucket_end_time, source_bucket_size
        )
        for row in data:
            FeatureEvaluationBucket.objects.create(
                environment_id=row["environment_id"],
                feature_name=row["feature_name"],
                total_count=row["count"],
                bucket_size=bucket_size,
                created_at=bucket_start_time,
            )


def _get_api_usage_source_data(
    process_from: datetime, process_till: datetime, source_bucket_size: int = None
) -> dict:
    filters = Q(
        created_at__lte=process_till,
        created_at__gt=process_from,
    )
    if source_bucket_size:
        return (
            APIUsageBucket.objects.filter(filters, bucket_size=source_bucket_size)
            .values("environment_id", "resource")
            .annotate(count=Sum("total_count"))
        )
    return (
        APIUsageRaw.objects.filter(filters)
        .values("environment_id", "resource")
        .annotate(count=Count("id"))
    )


def _get_feature_evaluation_source_data(
    process_from: datetime, process_till: datetime, source_bucket_size: int = None
) -> dict:
    filters = Q(
        created_at__lte=process_till,
        created_at__gt=process_from,
    )
    if source_bucket_size:
        return (
            FeatureEvaluationBucket.objects.filter(
                filters, bucket_size=source_bucket_size
            )
            .values("environment_id", "feature_name")
            .annotate(count=Sum("total_count"))
        )
    return (
        FeatureEvaluationRaw.objects.filter(filters)
        .values("environment_id", "feature_name")
        .annotate(count=Sum("evaluation_count"))
    )
