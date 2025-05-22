from datetime import date, datetime, timedelta
from typing import List

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db.models import Sum
from django.utils import timezone

from app_analytics.dataclasses import FeatureEvaluationData, UsageData
from app_analytics.influxdb_wrapper import (
    get_events_for_organisation,
)
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
from environments.models import Environment
from features.models import Feature
from organisations.models import Organisation

from . import constants
from .types import PERIOD_TYPE


def get_usage_data(
    organisation: Organisation,
    environment_id: int | None = None,
    project_id: int | None = None,
    period: PERIOD_TYPE | None = None,
) -> list[UsageData]:
    now = timezone.now()

    date_start = date_stop = None

    match period:
        case constants.CURRENT_BILLING_PERIOD:
            if not getattr(organisation, "subscription_information_cache", None):
                starts_at = now - timedelta(days=30)
            else:
                sub_cache = organisation.subscription_information_cache
                starts_at = sub_cache.current_billing_term_starts_at or now - timedelta(
                    days=30
                )
            month_delta = relativedelta(now, starts_at).months
            date_start = relativedelta(months=month_delta) + starts_at
            date_stop = now

        case constants.PREVIOUS_BILLING_PERIOD:
            if not getattr(organisation, "subscription_information_cache", None):
                starts_at = now - timedelta(days=30)
            else:
                sub_cache = organisation.subscription_information_cache
                starts_at = sub_cache.current_billing_term_starts_at or now - timedelta(
                    days=30
                )
            month_delta = relativedelta(now, starts_at).months - 1
            month_delta += relativedelta(now, starts_at).years * 12
            date_start = relativedelta(months=month_delta) + starts_at
            date_stop = relativedelta(months=month_delta + 1) + starts_at

        case constants.NINETY_DAY_PERIOD:
            date_start = now - relativedelta(days=90)
            date_stop = now

    if settings.USE_POSTGRES_FOR_ANALYTICS:
        kwargs = {
            "organisation": organisation,
            "environment_id": environment_id,
            "project_id": project_id,
        }

        if date_start:
            assert date_stop
            kwargs["date_start"] = date_start  # type: ignore[assignment]
            kwargs["date_stop"] = date_stop  # type: ignore[assignment]

        return get_usage_data_from_local_db(**kwargs)  # type: ignore[arg-type]

    kwargs = {
        "organisation_id": organisation.id,
        "environment_id": environment_id,
        "project_id": project_id,
    }

    if date_start:
        assert date_stop
        kwargs["date_start"] = date_start  # type: ignore[assignment]
        kwargs["date_stop"] = date_stop  # type: ignore[assignment]

    return get_usage_data_from_influxdb(**kwargs)  # type: ignore[arg-type]


def get_usage_data_from_local_db(
    organisation: Organisation,
    environment_id: int | None = None,
    project_id: int | None = None,
    date_start: datetime | None = None,
    date_stop: datetime | None = None,
) -> List[UsageData]:
    if date_start is None:
        date_start = timezone.now() - timedelta(days=30)
    if date_stop is None:
        date_stop = timezone.now()

    qs = APIUsageBucket.objects.filter(
        environment_id__in=_get_environment_ids_for_org(organisation),
        bucket_size=constants.ANALYTICS_READ_BUCKET_SIZE,
    )
    if project_id:
        environment_ids = Environment.objects.filter(project_id=project_id).values_list(
            "id", flat=True
        )
        # evaluate the queryset because analytics db does not have
        # access to environment/project table
        environment_ids = list(environment_ids)
        qs = qs.filter(environment_id__in=environment_ids)

    if environment_id:
        qs = qs.filter(environment_id=environment_id)

    qs = (
        qs.filter(  # type: ignore[assignment]
            created_at__date__lte=date_stop,
            created_at__date__gt=date_start,
        )
        .order_by("created_at__date")
        .values("created_at__date", "resource")
        .annotate(count=Sum("total_count"))
    )
    data_by_day = {}
    for row in qs:  # TODO Write proper mappers for this?
        day = row["created_at__date"]
        if day not in data_by_day:
            data_by_day[day] = UsageData(day=day)
        if column_name := Resource(row["resource"]).column_name:
            setattr(
                data_by_day[day],
                column_name,
                row["count"],
            )

    return data_by_day.values()  # type: ignore[return-value]


def get_total_events_count(organisation) -> int:  # type: ignore[no-untyped-def]
    """
    Return total number of events for an organisation in the last 30 days
    """
    if settings.USE_POSTGRES_FOR_ANALYTICS:
        count = APIUsageBucket.objects.filter(
            environment_id__in=_get_environment_ids_for_org(organisation),
            created_at__date__lte=date.today(),
            created_at__date__gt=date.today() - timedelta(days=30),
            bucket_size=constants.ANALYTICS_READ_BUCKET_SIZE,
        ).aggregate(total_count=Sum("total_count"))["total_count"]
    else:
        count = get_events_for_organisation(organisation.id)
    return count  # type: ignore[no-any-return]


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
            bucket_size=constants.ANALYTICS_READ_BUCKET_SIZE,
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


def _get_environment_ids_for_org(organisation) -> List[int]:  # type: ignore[no-untyped-def]
    # We need to do this to prevent Django from generating a query that
    # references the environments and projects tables,
    # as they do not exist in the analytics database.
    return [
        e.id for e in Environment.objects.filter(project__organisation=organisation)
    ]
