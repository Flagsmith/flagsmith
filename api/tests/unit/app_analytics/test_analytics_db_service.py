from datetime import UTC, date, datetime, timedelta

import pytest
from django.conf import settings
from django.utils import timezone
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture
from rest_framework.exceptions import NotFound

from app_analytics.analytics_db_service import (
    get_feature_evaluation_data,
    get_feature_evaluation_data_from_local_db,
    get_total_events_count,
    get_usage_data,
    get_usage_data_from_local_db,
)
from app_analytics.constants import (
    CURRENT_BILLING_PERIOD,
    PREVIOUS_BILLING_PERIOD,
)
from app_analytics.models import (
    APIUsageBucket,
    FeatureEvaluationBucket,
    Resource,
)
from environments.models import Environment
from features.models import Feature
from organisations.models import (
    Organisation,
    OrganisationSubscriptionInformationCache,
)
from projects.models import Project


@pytest.fixture
def cache(organisation: Organisation) -> OrganisationSubscriptionInformationCache:  # type: ignore[misc]
    yield OrganisationSubscriptionInformationCache.objects.create(
        organisation=organisation,
        current_billing_term_starts_at=timezone.now() - timedelta(days=20),
        current_billing_term_ends_at=timezone.now() + timedelta(days=10),
        api_calls_24h=2000,
        api_calls_7d=12000,
        api_calls_30d=38000,
        allowed_seats=5,
        allowed_30d_api_calls=40000,
    )


@pytest.mark.skipif(
    "analytics" not in settings.DATABASES,
    reason="Skip test if analytics database is configured",
)
@pytest.mark.django_db(databases=["analytics", "default"])
def test_get_usage_data_from_local_db(organisation, environment, settings):  # type: ignore[no-untyped-def]
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
def test_get_usage_data_from_local_db_project_id_filter(  # type: ignore[no-untyped-def]
    organisation: Organisation,
    project: Project,
    project_two: Project,
    environment: Environment,
    environment_two: Environment,
    project_two_environment: Environment,
    settings: SettingsWrapper,
):
    # Given
    environment_id = environment.id
    now = timezone.now()
    read_bucket_size = 15
    settings.ANALYTICS_BUCKET_SIZE = read_bucket_size
    total_count = 10

    # crate one bucket for every environment
    for environment_id in [
        environment.id,
        environment_two.id,
        project_two_environment.id,
    ]:
        APIUsageBucket.objects.create(
            environment_id=environment_id,
            resource=Resource.FLAGS,
            total_count=total_count,
            bucket_size=read_bucket_size,
            created_at=now,
        )
    # When
    usage_data_for_project_one = get_usage_data_from_local_db(
        organisation, project_id=project.id
    )
    usage_data_for_project_two = get_usage_data_from_local_db(
        organisation, project_id=project_two.id
    )

    # Then
    assert len(usage_data_for_project_one) == 1
    assert len(usage_data_for_project_two) == 1
    assert (
        list(usage_data_for_project_one)[0].flags == total_count * 2
    )  # 2 environments
    assert list(usage_data_for_project_two)[0].flags == total_count  # 1 environment


@pytest.mark.skipif(
    "analytics" not in settings.DATABASES,
    reason="Skip test if analytics database is configured",
)
@pytest.mark.django_db(databases=["analytics", "default"])
def test_get_total_events_count(organisation, environment, settings):  # type: ignore[no-untyped-def]
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
def test_get_feature_evaluation_data_from_local_db(  # type: ignore[no-untyped-def]
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


def test_get_usage_data_calls_get_usage_data_from_influxdb_if_postgres_not_configured(  # type: ignore[no-untyped-def]
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


def test_get_usage_data_calls_get_usage_data_from_local_db_if_postgres_is_configured(  # type: ignore[no-untyped-def]
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


def test_get_total_events_count_calls_influx_method_if_postgres_not_configured(  # type: ignore[no-untyped-def]
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


def test_get_feature_evaluation_data_calls_influx_method_if_postgres_not_configured(  # type: ignore[no-untyped-def]
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


def test_get_feature_evaluation_data_calls_get_feature_evaluation_data_from_local_db_if_configured(  # type: ignore[no-untyped-def]  # noqa: E501
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


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
@pytest.mark.parametrize("period", [PREVIOUS_BILLING_PERIOD, CURRENT_BILLING_PERIOD])
def test_get_usage_data_returns_404_when_organisation_has_no_billing_periods(
    mocker: MockerFixture,
    settings: SettingsWrapper,
    organisation: Organisation,
    period: str,
) -> None:
    # Given
    settings.USE_POSTGRES_FOR_ANALYTICS = True
    mocked_get_usage_data_from_local_db = mocker.patch(
        "app_analytics.analytics_db_service.get_usage_data_from_local_db", autospec=True
    )
    assert getattr(organisation, "subscription_information_cache", None) is None

    # When / Then
    with pytest.raises(NotFound) as e:
        get_usage_data(organisation, period=period)

    assert "No billing periods found for this organisation." in str(e)
    mocked_get_usage_data_from_local_db.assert_not_called()


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_get_usage_data_calls_get_usage_data_from_local_db_with_set_period_starts_at_with_current_billing_period(
    mocker: MockerFixture,
    settings: SettingsWrapper,
    organisation: Organisation,
    cache: OrganisationSubscriptionInformationCache,
) -> None:
    # Given
    period: str = CURRENT_BILLING_PERIOD
    settings.USE_POSTGRES_FOR_ANALYTICS = True
    mocked_get_usage_data_from_local_db = mocker.patch(
        "app_analytics.analytics_db_service.get_usage_data_from_local_db", autospec=True
    )

    assert getattr(organisation, "subscription_information_cache", None) == cache

    # When
    get_usage_data(organisation, period=period)

    # Then
    mocked_get_usage_data_from_local_db.assert_called_once_with(
        organisation=organisation,
        environment_id=None,
        project_id=None,
        date_start=datetime(2022, 12, 30, 9, 9, 47, 325132, tzinfo=UTC),
        date_stop=datetime(2023, 1, 19, 9, 9, 47, 325132, tzinfo=UTC),
    )


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_get_usage_data_calls_get_usage_data_from_local_db_with_set_period_starts_at_with_previous_billing_period(
    mocker: MockerFixture,
    settings: SettingsWrapper,
    organisation: Organisation,
    cache: OrganisationSubscriptionInformationCache,
) -> None:
    # Given
    period: str = PREVIOUS_BILLING_PERIOD

    settings.USE_POSTGRES_FOR_ANALYTICS = True
    mocked_get_usage_data_from_local_db = mocker.patch(
        "app_analytics.analytics_db_service.get_usage_data_from_local_db", autospec=True
    )

    assert getattr(organisation, "subscription_information_cache", None) == cache

    # When
    get_usage_data(organisation, period=period)

    # Then
    mocked_get_usage_data_from_local_db.assert_called_once_with(
        organisation=organisation,
        environment_id=None,
        project_id=None,
        date_start=datetime(2022, 11, 30, 9, 9, 47, 325132, tzinfo=UTC),
        date_stop=datetime(2022, 12, 30, 9, 9, 47, 325132, tzinfo=UTC),
    )
