from datetime import date, timedelta
from typing import List

from app_analytics.dataclasses import FeatureEvaluationData, UsageData
from app_analytics.influxdb_wrapper import get_events_for_organisation
from app_analytics.influxdb_wrapper import (
    get_feature_evaluation_data as get_feature_evaluation_data_from_influxdb,
)
from app_analytics.influxdb_wrapper import (
    get_usage_data as get_usage_data_from_influxdb,
)
from app_analytics.models import (
    APIUsageBucket,
    FeatureEvaluationBucket,
    Resource,
)
from django.conf import settings
from django.db.models import Sum
from django.utils import timezone

from environments.models import Environment
from features.models import Feature

ANALYTICS_READ_BUCKET_SIZE = 15


def get_usage_data(
    organisation, environment_id=None, project_id=None
) -> List[UsageData]:
    if settings.USE_POSTGRES_FOR_ANALYTICS:
        return get_usage_data_from_local_db(
            organisation, environment_id=environment_id, project_id=project_id
        )
    return get_usage_data_from_influxdb(
        organisation.id, environment_id=environment_id, project_id=project_id
    )


def get_usage_data_from_local_db(
    organisation, environment_id=None, project_id=None, period: int = 30
) -> List[UsageData]:
    qs = APIUsageBucket.objects.filter(
        environment_id__in=_get_environment_ids_for_org(organisation),
        bucket_size=ANALYTICS_READ_BUCKET_SIZE,
    )
    if project_id:
        qs = qs.filter(project_id=project_id)
    if environment_id:
        qs = qs.filter(environment_id=environment_id)

    qs = (
        qs.filter(
            created_at__date__lte=timezone.now(),
            created_at__date__gt=timezone.now() - timedelta(days=30),
        )
        .order_by("created_at__date")
        .values("created_at__date", "resource")
        .annotate(count=Sum("total_count"))
    )
    data_by_day = {}
    for row in qs:
        day = row["created_at__date"]
        if day not in data_by_day:
            data_by_day[day] = UsageData(day=day)
        setattr(
            data_by_day[day],
            Resource.get_lowercased_name(row["resource"]),
            row["count"],
        )

    return data_by_day.values()


def get_total_events_count(organisation) -> int:
    """
    Return total number of events for an organisation in the last 30 days
    """
    if settings.USE_POSTGRES_FOR_ANALYTICS:
        count = APIUsageBucket.objects.filter(
            environment_id__in=_get_environment_ids_for_org(organisation),
            created_at__date__lte=date.today(),
            created_at__date__gt=date.today() - timedelta(days=30),
            bucket_size=ANALYTICS_READ_BUCKET_SIZE,
        ).aggregate(total_count=Sum("total_count"))["total_count"]
    else:
        count = get_events_for_organisation(organisation.id)
    return count


def get_feature_evaluation_data(
    feature: Feature, environment_id: int, period: int = 30
) -> List[FeatureEvaluationData]:
    if settings.USE_POSTGRES_FOR_ANALYTICS:
        return get_feature_evaluation_data_from_local_db(
            feature, environment_id, period
        )
    return get_feature_evaluation_data_from_influxdb(
        feature_name=feature.name, environment_id=environment_id, period=f"{period}d"
    )


def get_feature_evaluation_data_from_local_db(
    feature: Feature, environment_id: int, period: int = 30
) -> List[FeatureEvaluationData]:
    feature_evaluation_data = (
        FeatureEvaluationBucket.objects.filter(
            environment_id=environment_id,
            bucket_size=ANALYTICS_READ_BUCKET_SIZE,
            feature_name=feature.name,
            created_at__date__lte=timezone.now(),
            created_at__date__gt=timezone.now() - timedelta(days=period),
        )
        .order_by("created_at__date")
        .values("created_at__date", "feature_name", "environment_id")
        .annotate(count=Sum("total_count"))
    )
    usage_list = []
    for data in feature_evaluation_data:
        usage_list.append(
            FeatureEvaluationData(
                day=data["created_at__date"],
                count=data["count"],
            )
        )
    return usage_list


def _get_environment_ids_for_org(organisation) -> List[int]:
    # We need to do this to prevent Django from generating a query that
    # references the environments and projects tables,
    # as they do not exist in the analytics database.
    return [
        e.id for e in Environment.objects.filter(project__organisation=organisation)
    ]
