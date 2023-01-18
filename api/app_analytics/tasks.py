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
        created_at__gte=process_from,
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


@register_task_handler()
def populate_bucket(
    bucket_size: int = 30, process_last: int = 60 * 5, source_bucket_size: int = None
):
    current_time = timezone.now().replace(second=0, microsecond=0)
    if bucket_size >= 60:
        current_time = current_time.replace(minute=0)

    process_till = current_time

    for i in range(1, (process_last // bucket_size) + 1):
        process_from = current_time - timezone.timedelta(minutes=i * bucket_size)
        data = get_source_data(process_from, process_till, source_bucket_size)
        for row in data:
            APIUsageBucket.objects.create(
                environment_id=row["environment_id"],
                resource=row["resource"],
                total_count=row["count"],
                bucket_size=bucket_size,
                created_at=process_from,
            )

        process_till = process_from
