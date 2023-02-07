from datetime import date, timedelta

import pytest
from app_analytics.analytics_db_service import (
    get_feature_evaluation_data_from_local_db,
    get_total_events_count,
    get_usage_data_from_local_db,
)
from app_analytics.models import (
    APIUsageBucket,
    FeatureEvaluationBucket,
    Resource,
)
from django.conf import settings
from django.utils import timezone


@pytest.mark.skipif(
    "analytics" not in settings.DATABASES,
    reason="Skip test if analytics database is configured",
)
@pytest.mark.django_db(databases=["analytics", "default"])
def test_get_usage_data_from_local_db(organisation, environment, settings):
    environment_id = environment.id
    now = timezone.now()
    read_bucket_size = 15
    settings.ANALYTICS_BUCKET_SIZE = read_bucket_size

    # Given - some initial data
    for i in range(31):
        for resource in Resource:
            APIUsageBucket.objects.create(
                environment_id=environment_id,
                resource=resource,
                total_count=10,
                bucket_size=read_bucket_size,
                created_at=now - timedelta(days=i),
            )
            # some data in different bucket
            APIUsageBucket.objects.create(
                environment_id=environment_id,
                resource=resource,
                total_count=10,
                bucket_size=read_bucket_size - 1,
                created_at=now - timedelta(days=i),
            )
            # some data in different environment
            APIUsageBucket.objects.create(
                environment_id=999999,
                resource=resource,
                total_count=10,
                bucket_size=read_bucket_size,
                created_at=now - timedelta(days=i),
            )

    # When
    usage_data_list = get_usage_data_from_local_db(organisation)

    # Then
    assert len(usage_data_list) == 30
    today = date.today()
    for count, data in enumerate(usage_data_list):
        assert data.flags == 10
        assert data.environment_document == 10
        assert data.identities == 10
        assert data.traits == 10
        assert data.day == today - timedelta(days=29 - count)


@pytest.mark.skipif(
    "analytics" not in settings.DATABASES,
    reason="Skip test if analytics database is configured",
)
@pytest.mark.django_db(databases=["analytics", "default"])
def test_get_total_events_count(organisation, environment, settings):
    settings.USE_POSTGRES_FOR_ANALYTICS = True
    environment_id = environment.id
    now = timezone.now()
    read_bucket_size = 15
    settings.ANALYTICS_BUCKET_SIZE = read_bucket_size

    # Given - some initial data
    for i in range(31):
        for resource in Resource:
            APIUsageBucket.objects.create(
                environment_id=environment_id,
                resource=resource,
                total_count=10,
                bucket_size=read_bucket_size,
                created_at=now - timedelta(days=i),
            )
            # some data in different bucket
            APIUsageBucket.objects.create(
                environment_id=environment_id,
                resource=resource,
                total_count=10,
                bucket_size=read_bucket_size - 1,
                created_at=now - timedelta(days=i),
            )
            # some data in different environment
            APIUsageBucket.objects.create(
                environment_id=999999,
                resource=resource,
                total_count=10,
                bucket_size=read_bucket_size,
                created_at=now - timedelta(days=i),
            )
    # When
    total_events_count = get_total_events_count(organisation)

    # Then
    assert total_events_count == 10 * len(Resource) * 30


@pytest.mark.skipif(
    "analytics" not in settings.DATABASES,
    reason="Skip test if analytics database is configured",
)
@pytest.mark.django_db(databases=["analytics", "default"])
def test_get_feature_evaluation_data_from_local_db(feature, environment, settings):
    environment_id = environment.id
    feature_name = feature.name
    now = timezone.now()
    read_bucket_size = 15
    settings.ANALYTICS_BUCKET_SIZE = read_bucket_size

    # Given - some initial data
    for i in range(31):
        FeatureEvaluationBucket.objects.create(
            environment_id=environment_id,
            feature_name=feature_name,
            total_count=10,
            bucket_size=read_bucket_size,
            created_at=now - timedelta(days=i),
        )
        # some data in different bucket
        FeatureEvaluationBucket.objects.create(
            environment_id=environment_id,
            feature_name=feature_name,
            total_count=10,
            bucket_size=read_bucket_size - 1,
            created_at=now - timedelta(days=i),
        )

        # some data in different environment
        FeatureEvaluationBucket.objects.create(
            environment_id=99999,
            feature_name=feature_name,
            total_count=10,
            bucket_size=read_bucket_size,
            created_at=now - timedelta(days=i),
        )

    # When
    usage_data_list = get_feature_evaluation_data_from_local_db(feature, environment_id)

    # Then
    assert len(usage_data_list) == 30
    today = date.today()
    for i, data in enumerate(usage_data_list):
        assert data.count == 10
        assert data.day == today - timedelta(days=29 - i)
