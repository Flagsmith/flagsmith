from datetime import date, timedelta
from typing import List

from app_analytics.influxdb_wrapper import (
    get_events_for_organisation,
    get_multiple_event_list_for_organisation,
)
from django.conf import settings
from django.db.models import Sum

from environments.models import Environment

from .models import APIUsageBucket, Resource
from .schemas import UsageData, UsageDataSchema

USAGE_READ_BUCKET_SIZE = 15


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
    environment_ids = Environment.objects.filter(
        project_id__in=organisation.projects.all().values_list("id", flat=True)
    ).values_list("id", flat=True)

    environment_ids = [id for id in environment_ids]

    qs = APIUsageBucket.objects.filter(
        environment_id__in=environment_ids, bucket_size=USAGE_READ_BUCKET_SIZE
    )
    if project_id:
        qs = qs.filter(project_id=project_id)
    if environment_id:
        qs = qs.filter(environment_id=environment_id)

    def get_count_from_qs(qs, resource) -> int:
        return next(
            filter(lambda obj: obj["resource"] == resource, qs),
            {},
        ).get("count", 0)

    usage_list = []
    today = date.today()
    for i in range(30):
        process_from = today - timedelta(days=i)
        process_till = process_from + timedelta(days=1)
        events = (
            qs.filter(
                created_at__date__gte=process_from, created_at__date__lt=process_till
            )
            .values("created_at__date", "resource")
            .annotate(count=Sum("total_count"))
        )
        usage_list.append(
            UsageData(
                day=process_from,
                flags=get_count_from_qs(events, Resource.FLAGS),
                identities=get_count_from_qs(events, Resource.IDENTITIES),
                traits=get_count_from_qs(events, Resource.TRAITS),
                environment_document=get_count_from_qs(
                    events, Resource.ENVIRONMENT_DOCUMENT
                ),
            )
        )
    return usage_list


def get_total_events_count(organisation) -> int:
    """
    Return total number of events for an organisation in the last 30 days
    """
    if settings.USE_CUSTOM_ANALYTICS:
        environment_ids = Environment.objects.filter(
            project_id__in=organisation.projects.all().values_list("id", flat=True)
        ).values_list("id", flat=True)

        environment_ids = [id for id in environment_ids]
        events = APIUsageBucket.objects.filter(
            environment_id__in=environment_ids,
            created_at__date__lte=date.today(),
            created_at__date__gt=date.today() - timedelta(days=30),
            bucket_size=USAGE_READ_BUCKET_SIZE,
        ).aggregate(total_count=Sum("total_count"))["total_count"]
    else:
        events = get_events_for_organisation(organisation.id)
    return events
