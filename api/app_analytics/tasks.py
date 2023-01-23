from datetime import datetime

from django.db.models import Count, Q, Sum
from django.utils import timezone

from environments.models import Environment
from task_processor.decorators import register_task_handler

from .models import APIUsageBucket, APIUsageRaw, FeatureEvaluation, Resource


@register_task_handler()
def track_feature_evaluation(environment_id, feature_evaluations):
    for feature_id, evaluation_count in feature_evaluations.items():
        kwargs = {"feature_id": feature_id, "environment_id": environment_id}
        FeatureEvaluation.objects.create(**kwargs)


# TODO: improve this
def get_resource_enum(resource):
    return {
        "flags": Resource.FLAGS,
        "identities": Resource.IDENTITIES,
        "traits": Resource.TRAITS,
        "environment_document": Resource.ENVIRONMENT_DOCUMENT,
    }.get(resource)


@register_task_handler()
def track_request(resource: str, host: str, environment_key: str):
    environment = Environment.get_from_cache(environment_key)
    if environment is None:
        return
    APIUsageRaw.objects.create(
        environment_id=environment.id,
        resource=get_resource_enum(resource),
        host=host,
    )


def get_source_data(
    process_from: datetime, process_till: datetime, source_bucket_size: int = None
):
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


def get_start_of_current_bucket(bucket_size: int):
    current_time = timezone.now().replace(second=0, microsecond=0)
    # calculate start of 'current' bucket
    start_of_current_bucket = current_time - timezone.timedelta(
        minutes=current_time.minute % bucket_size
    )
    return start_of_current_bucket


@register_task_handler()
def populate_bucket(bucket_size: int, run_every: int, source_bucket_size: int = None):
    start_of_current_bucket = get_start_of_current_bucket(
        bucket_size,
    )

    for i in range(1, (run_every // bucket_size) + 1):
        process_from = start_of_current_bucket - timezone.timedelta(
            minutes=bucket_size * i
        )
        process_to = process_from + timezone.timedelta(minutes=bucket_size)
        data = get_source_data(process_from, process_to, source_bucket_size)
        for row in data:
            APIUsageBucket.objects.create(
                environment_id=row["environment_id"],
                resource=row["resource"],
                total_count=row["count"],
                bucket_size=bucket_size,
                created_at=process_from,
            )
