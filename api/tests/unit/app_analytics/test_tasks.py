from datetime import datetime

import pytest
from app_analytics.models import APIUsageBucket, APIUsageRaw, Resource
from app_analytics.tasks import populate_bucket
from django.utils import timezone


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
@pytest.mark.django_db(databases=["analytics"])
def test_populate_bucket_15m_bucket(freezer):
    # Given
    environment_id = 1
    bucket_size = 15
    now = timezone.now()
    # let's create events at every 1 minutes
    # for the last two hours, i.e: from 9:09:47 to 7:10:47
    for i in range(60 * 2):
        create_events(environment_id, 1, now - timezone.timedelta(minutes=1 * i))
        # now = now - timezone.timedelta(minutes=1)

    # Next, let's go 1 hr back in the past and run this
    freezer.move_to(timezone.now() - timezone.timedelta(hours=1))
    populate_bucket(bucket_size, run_every=60)

    # Then - it should have created four buckets
    buckets = APIUsageBucket.objects.filter(bucket_size=15).order_by("created_at").all()

    assert len(buckets) == 4
    assert buckets[0].created_at.isoformat() == "2023-01-19T07:00:00+00:00"
    # since we started at 7:10:47, the first bucket should have 5 events
    assert buckets[0].total_count == 5

    # the rest of them should have 15 events
    assert buckets[1].created_at.isoformat() == "2023-01-19T07:15:00+00:00"
    assert buckets[1].total_count == 15

    assert buckets[2].created_at.isoformat() == "2023-01-19T07:30:00+00:00"
    assert buckets[2].total_count == 15

    assert buckets[3].created_at.isoformat() == "2023-01-19T07:45:00+00:00"
    assert buckets[3].total_count == 15

    # Now, let's move forward 1hr and run this again
    freezer.move_to(timezone.now() + timezone.timedelta(hours=1))
    populate_bucket(bucket_size, run_every=60)

    # Then - it should have created four more buckets
    buckets = APIUsageBucket.objects.filter(bucket_size=15).order_by("created_at").all()
    assert len(buckets) == 8

    # with 15 events each
    assert buckets[4].created_at.isoformat() == "2023-01-19T08:00:00+00:00"
    assert buckets[4].total_count == 15

    assert buckets[5].created_at.isoformat() == "2023-01-19T08:15:00+00:00"
    assert buckets[5].total_count == 15

    assert buckets[6].created_at.isoformat() == "2023-01-19T08:30:00+00:00"
    assert buckets[6].total_count == 15

    assert buckets[7].created_at.isoformat() == "2023-01-19T08:45:00+00:00"
    assert buckets[7].total_count == 15


@pytest.mark.parametrize(
    "bucket_size, runs_every",
    [(15, 60), (10, 60), (10, 30), (30, 30), (60, 60), (10, 10), (60, 60 * 4)],
)
@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
@pytest.mark.django_db(databases=["analytics"])
def test_populate_bucket(freezer, bucket_size, runs_every):
    # Given
    environment_id = 1
    now = timezone.now()
    # let's create events at every 1 minutes
    # for the last two hours, i.e: from 9:09:47
    for i in range(runs_every * 2):
        create_events(environment_id, 1, now - timezone.timedelta(minutes=1 * i))
        # create events in some other environments as well - just to make sure
        # we don't aggregate them in the same environment
        create_events(999, 1, now - timezone.timedelta(minutes=1 * i))

    # When
    populate_bucket(bucket_size, run_every=runs_every)

    # Then
    buckets = (
        APIUsageBucket.objects.filter(
            bucket_size=bucket_size,
            total_count=bucket_size,
            environment_id=environment_id,
        )
        .order_by("-created_at")
        .all()
    )

    assert len(buckets) == runs_every // bucket_size
    # and
    start_time = timezone.now().replace(minute=0, second=0, microsecond=0)
    for bucket in buckets:
        start_time = start_time - timezone.timedelta(minutes=bucket_size)
        assert bucket.created_at == start_time


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


@pytest.mark.freeze_time("2023-01-19T09:00:00+00:00")
@pytest.mark.django_db(databases=["analytics"])
def test_populate_bucket_using_a_bucket(freezer):
    # Given
    environment_id = 1

    # let's create 3 5m buckets
    now = timezone.now()
    for _ in range(3):
        APIUsageBucket.objects.create(
            environment_id=environment_id,
            resource=Resource.FLAGS,
            total_count=100,
            created_at=now,
            bucket_size=5,
        )
        now = now - timezone.timedelta(minutes=5)

    # move the time to 9:47
    freezer.move_to(timezone.now().replace(minute=47))

    # When
    populate_bucket(bucket_size=15, run_every=60, source_bucket_size=5)

    # Then
    assert APIUsageBucket.objects.filter(bucket_size=15, total_count=300).count() == 1
