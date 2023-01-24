from datetime import date, timedelta
from typing import List

from app_analytics.influxdb_wrapper import (
    get_events_for_organisation,
    get_multiple_event_list_for_organisation,
)
from django.conf import settings
from django.db.models import Sum

from .models import APIUsageByDay, Resource
from .schemas import UsageData, UsageDataSchema


def get_usage_data(
    organisation, environment_id=None, project_id=None
) -> List[UsageData]:
    if settings.USE_CUSTOM_ANALYTICS:
        return get_usage_data_from_local_db(
            organisation, environment_id=environment_id, project_id=project_id
        )
    return get_usage_data_from_influxdb(
        organisation, environment_id=environment_id, project_id=project_id
    )


def get_usage_data_from_influxdb(
    organisation, environment_id=None, project_id=None
) -> List[UsageData]:
    events_list = get_multiple_event_list_for_organisation(
        organisation.pk, environment_id, project_id
    )
    return UsageDataSchema(many=True).load(events_list)


def get_usage_data_from_local_db(
    organisation, environment_id=None, project_id=None
) -> List[UsageData]:
    if settings.USE_CUSTOM_ANALYTICS:
        qs = APIUsageByDay.objects.filter(
            environment_id__in=organisation.project.all().values_list(
                "environment_id", flat=True
            ),
            created_date=date.today() - timedelta(days=30),
        )
        if project_id:
            qs = qs.filter(project_id=project_id)
        if environment_id:
            qs = qs.filter(environment_id=environment_id)

        qs = qs.values("resource", "date", "total_count")

        def get_count_from_qs(qs, date, resource) -> int:
            return next(
                filter(
                    lambda obj: obj["date"] == date and obj["resource"] == resource, qs
                ),
                {},
            ).get_total_count(0)

        usage_list = []
        dates = set(obj["date"] for obj in qs)
        for day in dates:
            usage_list.append(
                UsageData(
                    flags=get_count_from_qs(qs, date, Resource.FLAGS),
                    day=day,
                    identities=get_count_from_qs(qs, date, Resource.IDENTITIES),
                    traits=get_count_from_qs(qs, date, Resource.TRAITS),
                    environment_document=get_count_from_qs(
                        qs, date, Resource.ENVIRONMENT_DOCUMENT
                    ),
                )
            )
        return usage_list


def get_total_events_count(organisation) -> int:
    """
    Return total number of events for an organisation in the last 30 days
    """
    if settings.USE_CUSTOM_ANALYTICS:
        events = APIUsageByDay.objects.filter(
            environment_id__in=organisation.project.all().values_list(
                "environment_id", flat=True
            ),
            date__lte=date.today(),
            date__gte=date.today() - timedelta(days=30),
        ).aggregate(total_count=Sum("total_count"))["total_count"]
    else:
        events = get_events_for_organisation(organisation.id)
    return events
