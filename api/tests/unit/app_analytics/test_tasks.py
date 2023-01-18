from datetime import datetime

import pytest
from app_analytics.models import APIUsageBucket, APIUsageRaw, Resource
from app_analytics.tasks import populate_bucket
from django.utils import timezone


@pytest.mark.django_db(databases=["analytics"])
def test_populate_bucket_15m_bucket():
    # Given
    environment_id = 1
    bucket_size = 15
    now = timezone.now()

    for _ in range(5):
        create_events(environment_id, 2, now)
        now = now - timezone.timedelta(minutes=15)

    # When
    populate_bucket(bucket_size, process_last=50)

    # Then
    assert APIUsageBucket.objects.filter(bucket_size=15).count() == 3

    # all three buckets are 15 minutes apart
    buckets = APIUsageBucket.objects.all().order_by("created_at")

    buckets[0].created_at == buckets[1].created_at + timezone.timedelta(
        minutes=15
    ) == buckets[0].created_at + timezone.timedelta(minutes=30)


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
    for _ in range(3):
        APIUsageBucket.objects.create(
            environment_id=environment_id,
            resource=Resource.FLAGS,
            total_count=100,
            created_at=now,
            bucket_size=5,
        )
        now = now - timezone.timedelta(minutes=5)

    # When
    populate_bucket(bucket_size=15, process_last=50, source_bucket_size=5)

    # Then
    assert APIUsageBucket.objects.filter(bucket_size=15, total_count=300).exists()
