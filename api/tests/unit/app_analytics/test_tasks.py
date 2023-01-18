from datetime import datetime

import pytest
from app_analytics.models import APIUsageBucket, APIUsageRaw, Resource
from app_analytics.tasks import populate_bucket
from django.utils import timezone


@pytest.mark.django_db(databases=["analytics"])
def test_populate_bucket_15m_bucket():
    pass
    # Given
    # environment_id = 1
    # # start now at -1 minutes for now events to be included
    # # in the first 15m buckets
    # now = timezone.now() - timezone.timedelta(minutes=1)
    # past_15m = now - timezone.timedelta(minutes=15)
    # past_30m = past_15m - timezone.timedelta(minutes=15)
    # past_45m = past_30m - timezone.timedelta(minutes=15)
    # past_60m = past_45m - timezone.timedelta(minutes=15)

    # # Two events in the first 15 minutes
    # now_events = create_events(environment_id, 2, now)

    # # Two events in the past 15 minutes
    # past_15m_events = create_events(environment_id, 2, past_15m)

    # # Two events in the past 30 minutes
    # past_30m_events = create_events(environment_id, 2, past_30m)

    # # Two events in the past 45 minutes
    # past_45m_events = create_events(environment_id, 2, past_30m)

    # # Two events in the past 60 minutes
    # past_60m_events = create_events(environment_id, 2, past_30m)

    # # When
    # populate_bucket(bucket_size=15, process_last=50)

    # # Then
    # assert APIUsageBucket.objects.count() == 3

    # There should be 3 buckets
    # first_bucket_created_at = timezone.now().replace(second=0, microsecond=0)
    # first_buckets = APIUsageBucket.objects.get(
    #     created_at=timezone.now().replace(second=0, microsecond=0)
    # )
    # for bucket in APIUsageBucket.objects.all():
    #     print("bucket -------->", bucket.created_at.isoformat())
    #     print("bucket -------->", bucket.total_count)


def create_events(environment_id: str, how_many: int, when: datetime):
    events = []
    for _ in range(how_many):
        event = APIUsageRaw.objects.create(
            environment_id=environment_id,
            host="host1",
            resource=Resource.FLAGS,
        )
        # update created_at
        event.created_at = when
        event.save()
        events.append(events)

    return events


@pytest.mark.django_db(databases=["analytics"])
def test_populate_bucket_using_a_bucket():
    # Given
    environment_id = 1
    # let's create 3 5m buckets
    now = timezone.now().replace(second=0, microsecond=0)
    buckets = []
    for i in range(3):
        bucket = APIUsageBucket.objects.create(
            environment_id=environment_id,
            resource=Resource.FLAGS,
            total_count=100,
            created_at=now,
            bucket_size=5,
        )
        now = now - timezone.timedelta(minutes=5)
        buckets.append(bucket)

    # When
    populate_bucket(bucket_size=15, process_last=50, source_bucket_size=5)

    # Then
    assert APIUsageBucket.objects.filter(bucket_size=15, total_count=300).exists()
