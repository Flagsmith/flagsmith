from datetime import date, timedelta

import pytest
from app_analytics.analytics_db_service import (
    get_feature_evaluation_data,
    get_feature_evaluation_data_from_local_db,
    get_total_events_count,
    get_usage_data,
    get_usage_data_from_local_db,
)
from app_analytics.models import (
    APIUsageBucket,
    FeatureEvaluationBucket,
    Resource,
)
from django.conf import settings
from django.utils import timezone
from pytest_django.fixtures import SettingsWrapper

from environments.models import Environment
from features.models import Feature


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
        bucket_created_at = now - timedelta(days=i)
        for resource in Resource:
            APIUsageBucket.objects.create(
                environment_id=environment_id,
                resource=resource,
                total_count=10,
                bucket_size=read_bucket_size,
                created_at=bucket_created_at,
            )
            # create another bucket after `read_bucket_size` minutes to make sure we have more than one bucket in day
            APIUsageBucket.objects.create(
                environment_id=environment_id,
                resource=resource,
                total_count=10,
                bucket_size=read_bucket_size,
                created_at=bucket_created_at - timedelta(minutes=read_bucket_size),
            )
            # some data in different bucket
            APIUsageBucket.objects.create(
                environment_id=environment_id,
                resource=resource,
                total_count=10,
                bucket_size=read_bucket_size - 1,
                created_at=bucket_created_at,
            )
            # some data in different environment
            APIUsageBucket.objects.create(
                environment_id=999999,
                resource=resource,
                total_count=10,
                bucket_size=read_bucket_size,
                created_at=bucket_created_at,
            )

    # When
    usage_data_list = get_usage_data_from_local_db(organisation)

    # Then
    assert len(usage_data_list) == 30
    today = date.today()
    for count, data in enumerate(usage_data_list):
        assert data.flags == 20
        assert data.environment_document == 20
        assert data.identities == 20
        assert data.traits == 20
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
        bucket_created_at = now - timedelta(days=i)
        for resource in Resource:
            APIUsageBucket.objects.create(
                environment_id=environment_id,
                resource=resource,
                total_count=10,
                bucket_size=read_bucket_size,
                created_at=bucket_created_at,
            )

            # create another bucket after `read_bucket_size` minutes to make sure we have more than one bucket in day
            APIUsageBucket.objects.create(
                environment_id=environment_id,
                resource=resource,
                total_count=10,
                bucket_size=read_bucket_size,
                created_at=bucket_created_at - timedelta(minutes=read_bucket_size),
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
    assert total_events_count == 20 * len(Resource) * 30


@pytest.mark.skipif(
    "analytics" not in settings.DATABASES,
    reason="Skip test if analytics database is configured",
)
@pytest.mark.django_db(databases=["analytics", "default"])
def test_get_feature_evaluation_data_from_local_db(
    feature: Feature, environment: Environment, settings: SettingsWrapper
):
    environment_id = environment.id
    feature_name = feature.name
    now = timezone.now()
    read_bucket_size = 15
    settings.ANALYTICS_BUCKET_SIZE = read_bucket_size

    # Given - some initial data
    for i in range(31):
        bucket_created_at = now - timedelta(days=i)
        FeatureEvaluationBucket.objects.create(
            environment_id=environment_id,
            feature_name=feature_name,
            total_count=10,
            bucket_size=read_bucket_size,
            created_at=bucket_created_at,
        )
        # create another bucket after `read_bucket_size` minutes to make sure we have more than one bucket in day
        FeatureEvaluationBucket.objects.create(
            environment_id=environment_id,
            feature_name=feature_name,
            total_count=10,
            bucket_size=read_bucket_size,
            created_at=bucket_created_at - timedelta(minutes=read_bucket_size),
        )
        # some data in different bucket
        FeatureEvaluationBucket.objects.create(
            environment_id=environment_id,
            feature_name=feature_name,
            total_count=10,
            bucket_size=read_bucket_size - 1,
            created_at=bucket_created_at,
        )

        # some data in different environment
        FeatureEvaluationBucket.objects.create(
            environment_id=99999,
            feature_name=feature_name,
            total_count=10,
            bucket_size=read_bucket_size,
            created_at=now - timedelta(days=i),
        )

        # some data for different feature
        FeatureEvaluationBucket.objects.create(
            environment_id=environment_id,
            feature_name="some_other_feature",
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
        assert data.count == 20
        assert data.day == today - timedelta(days=29 - i)


def test_get_usage_data_calls_get_usage_data_from_influxdb_if_postgres_not_configured(
    mocker, settings, organisation
):
    # Given
    settings.USE_POSTGRES_FOR_ANALYTICS = False
    mocked_get_usage_data_from_influxdb = mocker.patch(
        "app_analytics.analytics_db_service.get_usage_data_from_influxdb", autospec=True
    )

    # When
    usage_data = get_usage_data(organisation)

    # Then
    assert usage_data == mocked_get_usage_data_from_influxdb.return_value
    mocked_get_usage_data_from_influxdb.assert_called_once_with(
        organisation_id=organisation.id, environment_id=None, project_id=None
    )


def test_get_usage_data_calls_get_usage_data_from_local_db_if_postgres_is_configured(
    mocker, settings, organisation
):
    # Given
    settings.USE_POSTGRES_FOR_ANALYTICS = True
    mocked_get_usage_data_from_local_db = mocker.patch(
        "app_analytics.analytics_db_service.get_usage_data_from_local_db", autospec=True
    )

    # When
    usage_data = get_usage_data(organisation)

    # Then
    assert usage_data == mocked_get_usage_data_from_local_db.return_value
    mocked_get_usage_data_from_local_db.assert_called_once_with(
        organisation=organisation, environment_id=None, project_id=None
    )


def test_get_total_events_count_calls_influx_method_if_postgres_not_configured(
    mocker, settings, organisation
):
    # Given
    settings.USE_POSTGRES_FOR_ANALYTICS = False
    mocked_get_events_for_organisation = mocker.patch(
        "app_analytics.analytics_db_service.get_events_for_organisation", autospec=True
    )

    # When
    total_events_count = get_total_events_count(organisation)

    # Then
    assert total_events_count == mocked_get_events_for_organisation.return_value
    mocked_get_events_for_organisation.assert_called_once_with(
        organisation_id=organisation.id
    )


def test_get_feature_evaluation_data_calls_influx_method_if_postgres_not_configured(
    mocker, settings, organisation, feature, environment
):
    # Given
    settings.USE_POSTGRES_FOR_ANALYTICS = False
    mocked_get_feature_evaluation_data_from_influxdb = mocker.patch(
        "app_analytics.analytics_db_service.get_feature_evaluation_data_from_influxdb",
        autospec=True,
    )

    # When
    feature_evaluation_data = get_feature_evaluation_data(feature, environment.id)

    # Then
    assert (
        feature_evaluation_data
        == mocked_get_feature_evaluation_data_from_influxdb.return_value
    )
    mocked_get_feature_evaluation_data_from_influxdb.assert_called_once_with(
        feature_name=feature.name, environment_id=environment.id, period="30d"
    )


def test_get_feature_evaluation_data_calls_get_feature_evaluation_data_from_local_db_if_configured(
    mocker, settings, organisation, feature, environment
):
    # Given
    settings.USE_POSTGRES_FOR_ANALYTICS = True
    mocked_get_feature_evaluation_data_from_local_db = mocker.patch(
        "app_analytics.analytics_db_service.get_feature_evaluation_data_from_local_db",
        autospec=True,
    )

    # When
    feature_evaluation_data = get_feature_evaluation_data(feature, environment.id)

    # Then
    assert (
        feature_evaluation_data
        == mocked_get_feature_evaluation_data_from_local_db.return_value
    )
    mocked_get_feature_evaluation_data_from_local_db.assert_called_once_with(
        feature=feature, environment_id=environment.id, period=30
    )
