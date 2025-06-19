from datetime import date, datetime, timedelta
from logging import getLogger
from typing import TYPE_CHECKING, List

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.db.models import Q, Sum
from django.utils import timezone
from rest_framework.exceptions import NotFound

from app_analytics import constants
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
from app_analytics.mappers import map_annotated_api_usage_buckets_to_usage_data
from app_analytics.models import (
    APIUsageBucket,
    FeatureEvaluationBucket,
)
from app_analytics.types import Labels, PeriodType
from environments.models import Environment
from features.models import Feature
from organisations.models import Organisation, OrganisationSubscriptionInformationCache

logger = getLogger(__name__)


def get_usage_data(
    organisation: Organisation,
    environment_id: int | None = None,
    project_id: int | None = None,
    period: PeriodType | None = None,
    labels_filter: Labels | None = None,
) -> list[UsageData]:
    sub_cache = OrganisationSubscriptionInformationCache.objects.filter(
        organisation=organisation
    ).first()

    date_start, date_stop = _get_start_date_and_stop_date_for_subscribed_organisation(
        sub_cache=sub_cache,
        period=period,
    )

    if settings.USE_POSTGRES_FOR_ANALYTICS:
        return get_usage_data_from_local_db(
            organisation=organisation,
            environment_id=environment_id,
            project_id=project_id,
            date_start=date_start,
            date_stop=date_stop,
            labels_filter=labels_filter,
        )

    if settings.INFLUXDB_TOKEN:
        return get_usage_data_from_influxdb(
            organisation_id=organisation.id,
            environment_id=environment_id,
            project_id=project_id,
            date_start=date_start,
            date_stop=date_stop,
            labels_filter=labels_filter,
        )

    logger.warning(constants.NO_ANALYTICS_DATABASE_CONFIGURED_WARNING)
    return []


def get_usage_data_from_local_db(
    organisation: Organisation,
    environment_id: int | None = None,
    project_id: int | None = None,
    date_start: datetime | None = None,
    date_stop: datetime | None = None,
    labels_filter: Labels | None = None,
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

    if labels_filter:
        qs = qs.filter(labels__contains=labels_filter)

    qs = (
        qs.filter(  # type: ignore[assignment]
            created_at__date__lte=date_stop,
            created_at__date__gt=date_start,
        )
        .order_by("created_at__date")
        .values("created_at__date", "resource", "labels")
        .annotate(count=Sum("total_count"))
    )

    return map_annotated_api_usage_buckets_to_usage_data(qs)


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
    feature: Feature,
    environment_id: int,
    period: int = 30,
    labels_filter: Labels | None = None,
) -> List[FeatureEvaluationData]:
    if settings.USE_POSTGRES_FOR_ANALYTICS:
        return get_feature_evaluation_data_from_local_db(
            feature=feature,
            environment_id=environment_id,
            period=period,
            labels_filter=labels_filter,
        )

    if settings.INFLUXDB_TOKEN:
        return get_feature_evaluation_data_from_influxdb(
            feature_name=feature.name,
            environment_id=environment_id,
            period=f"{period}d",
            labels_filter=labels_filter,
        )

    logger.warning(constants.NO_ANALYTICS_DATABASE_CONFIGURED_WARNING)
    return []


def get_feature_evaluation_data_from_local_db(
    feature: Feature,
    environment_id: int,
    period: int = 30,
    labels_filter: Labels | None = None,
) -> List[FeatureEvaluationData]:
    filter = Q(
        environment_id=environment_id,
        bucket_size=constants.ANALYTICS_READ_BUCKET_SIZE,
        feature_name=feature.name,
        created_at__date__lte=timezone.now(),
        created_at__date__gt=timezone.now() - timedelta(days=period),
    )
    if labels_filter:
        filter &= Q(labels__contains=labels_filter)
    feature_evaluation_data = (
        FeatureEvaluationBucket.objects.filter(filter)
        .order_by("created_at__date")
        .values("created_at__date", "feature_name", "environment_id", "labels")
        .annotate(count=Sum("total_count"))
    )
    usage_list = []
    for data in feature_evaluation_data:
        usage_list.append(
            FeatureEvaluationData(
                day=data["created_at__date"],
                count=data["count"],
                labels=data["labels"],
            )
        )
    return usage_list


def _get_environment_ids_for_org(organisation: Organisation) -> list[int]:
    # We need to do this to prevent Django from generating a query that
    # references the environments and projects tables,
    # as they do not exist in the analytics database.
    return [
        e.id for e in Environment.objects.filter(project__organisation=organisation)
    ]


def _get_start_date_and_stop_date_for_subscribed_organisation(
    sub_cache: OrganisationSubscriptionInformationCache | None,
    period: PeriodType | None = None,
) -> tuple[datetime | None, datetime | None]:
    """
    Populate start and stop date for the given period
    from the organisation's subscription information.
    """
    if period in {constants.CURRENT_BILLING_PERIOD, constants.PREVIOUS_BILLING_PERIOD}:
        if not (sub_cache and sub_cache.is_billing_terms_dates_set()):
            raise NotFound("No billing periods found for this organisation.")

    if TYPE_CHECKING:
        assert sub_cache

    now = timezone.now()

    match period:
        case constants.CURRENT_BILLING_PERIOD:
            starts_at = sub_cache.current_billing_term_starts_at or now - timedelta(
                days=30
            )
            month_delta = relativedelta(now, starts_at).months
            date_start = relativedelta(months=month_delta) + starts_at
            date_stop = now

        case constants.PREVIOUS_BILLING_PERIOD:
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

        case _:
            return None, None

    return date_start, date_stop
