import json
from datetime import date, timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture
from rest_framework import status
from rest_framework.test import APIClient

from app_analytics.constants import (
    CURRENT_BILLING_PERIOD,
    NINETY_DAY_PERIOD,
    PREVIOUS_BILLING_PERIOD,
)
from app_analytics.dataclasses import UsageData
from app_analytics.models import FeatureEvaluationRaw
from environments.identities.models import Identity
from environments.models import Environment
from features.models import Feature
from organisations.models import (
    Organisation,
    OrganisationSubscriptionInformationCache,
)


def test_sdk_analytics_ignores_bad_data(
    mocker: MockerFixture,
    environment: Environment,
    feature: Feature,
    api_client: APIClient,
) -> None:
    # Given
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)

    data = {"invalid_feature_name": 20, feature.name: 2}
    mocked_feature_eval_cache = mocker.patch(
        "app_analytics.views.feature_evaluation_cache"
    )

    url = reverse("api-v1:analytics-flags")

    # When
    response = api_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert mocked_feature_eval_cache.track_feature_evaluation.call_count == 1

    mocked_feature_eval_cache.track_feature_evaluation.assert_called_once_with(
        environment_id=environment.id,
        feature_name=feature.name,
        evaluation_count=data[feature.name],
        labels={},
    )


def test_get_usage_data(mocker, admin_client, organisation):  # type: ignore[no-untyped-def]
    # Given
    url = reverse("api-v1:organisations:usage-data", args=[organisation.id])

    mocked_get_usage_data = mocker.patch(
        "app_analytics.views.get_usage_data",
        autospec=True,
        return_value=[
            UsageData(flags=10, day=date.today()),
            UsageData(flags=10, day=date.today() - timedelta(days=1)),
        ],
    )

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [
        {
            "flags": 10,
            "day": str(date.today()),
            "identities": 0,
            "traits": 0,
            "environment_document": 0,
            "labels": None,
        },
        {
            "flags": 10,
            "day": str(date.today() - timedelta(days=1)),
            "identities": 0,
            "traits": 0,
            "environment_document": 0,
            "labels": None,
        },
    ]
    mocked_get_usage_data.assert_called_once_with(organisation, period=None)


@pytest.mark.freeze_time("2024-04-30T09:09:47.325132+00:00")
def test_get_usage_data__current_billing_period(
    settings: SettingsWrapper,
    mocker: MockerFixture,
    admin_client_new: APIClient,
    organisation: Organisation,
) -> None:
    # Given
    settings.INFLUXDB_TOKEN = "test-token"

    url = reverse("api-v1:organisations:usage-data", args=[organisation.id])
    url += f"?period={CURRENT_BILLING_PERIOD}"

    mocked_get_usage_data = mocker.patch(
        "app_analytics.analytics_db_service.get_usage_data_from_influxdb",
        autospec=True,
        return_value=[
            UsageData(flags=10, day=date.today()),
            UsageData(
                flags=10,
                day=date.today() - timedelta(days=1),
                labels={"client_application_name": "test-app"},
            ),
        ],
    )

    now = timezone.now()
    week_from_now = now + timedelta(days=7)
    four_weeks_ago = now - timedelta(days=28)

    OrganisationSubscriptionInformationCache.objects.create(
        organisation=organisation,
        current_billing_term_starts_at=four_weeks_ago,
        current_billing_term_ends_at=week_from_now,
        allowed_30d_api_calls=1_000_000,
    )

    # When
    response = admin_client_new.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [
        {
            "flags": 10,
            "day": str(date.today()),
            "identities": 0,
            "traits": 0,
            "environment_document": 0,
            "labels": None,
        },
        {
            "flags": 10,
            "day": str(date.today() - timedelta(days=1)),
            "identities": 0,
            "traits": 0,
            "environment_document": 0,
            "labels": {
                "client_application_name": "test-app",
                "client_application_version": None,
            },
        },
    ]

    mocked_get_usage_data.assert_called_once_with(
        organisation_id=organisation.id,
        environment_id=None,
        project_id=None,
        date_start=four_weeks_ago,
        date_stop=now,
        labels_filter=None,
    )


@pytest.mark.freeze_time("2024-04-30T09:09:47.325132+00:00")
def test_get_usage_data__previous_billing_period(
    mocker: MockerFixture,
    admin_client_new: APIClient,
    organisation: Organisation,
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.INFLUXDB_TOKEN = "test-token"

    url = reverse("api-v1:organisations:usage-data", args=[organisation.id])
    url += f"?period={PREVIOUS_BILLING_PERIOD}"

    mocked_get_usage_data = mocker.patch(
        "app_analytics.analytics_db_service.get_usage_data_from_influxdb",
        autospec=True,
        return_value=[
            UsageData(flags=10, day=date.today() - timedelta(days=29)),
            UsageData(flags=10, day=date.today() - timedelta(days=30)),
        ],
    )

    now = timezone.now()
    week_from_now = now + timedelta(days=7)
    four_weeks_ago = now - timedelta(days=28)
    target_start_at = now - timedelta(days=59)

    OrganisationSubscriptionInformationCache.objects.create(
        organisation=organisation,
        current_billing_term_starts_at=four_weeks_ago,
        current_billing_term_ends_at=week_from_now,
        allowed_30d_api_calls=1_000_000,
    )

    # When
    response = admin_client_new.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [
        {
            "flags": 10,
            "day": str(date.today() - timedelta(days=29)),
            "identities": 0,
            "traits": 0,
            "environment_document": 0,
            "labels": None,
        },
        {
            "flags": 10,
            "day": str(date.today() - timedelta(days=30)),
            "identities": 0,
            "traits": 0,
            "environment_document": 0,
            "labels": None,
        },
    ]

    mocked_get_usage_data.assert_called_once_with(
        organisation_id=organisation.id,
        environment_id=None,
        project_id=None,
        date_start=target_start_at,
        date_stop=four_weeks_ago,
        labels_filter=None,
    )


@pytest.mark.freeze_time("2024-04-30T09:09:47.325132+00:00")
def test_get_usage_data__ninety_day_period(
    settings: SettingsWrapper,
    mocker: MockerFixture,
    admin_client_new: APIClient,
    organisation: Organisation,
) -> None:
    # Given
    settings.INFLUXDB_TOKEN = "test-token"

    url = reverse("api-v1:organisations:usage-data", args=[organisation.id])
    url += f"?period={NINETY_DAY_PERIOD}"

    mocked_get_usage_data = mocker.patch(
        "app_analytics.analytics_db_service.get_usage_data_from_influxdb",
        autospec=True,
        return_value=[
            UsageData(flags=10, day=date.today()),
            UsageData(flags=10, day=date.today() - timedelta(days=1)),
        ],
    )

    now = timezone.now()
    week_from_now = now + timedelta(days=7)
    four_weeks_ago = now - timedelta(days=28)
    ninety_days_ago = now - timedelta(days=90)

    OrganisationSubscriptionInformationCache.objects.create(
        organisation=organisation,
        current_billing_term_starts_at=four_weeks_ago,
        current_billing_term_ends_at=week_from_now,
        allowed_30d_api_calls=1_000_000,
    )

    # When
    response = admin_client_new.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [
        {
            "flags": 10,
            "day": str(date.today()),
            "identities": 0,
            "traits": 0,
            "environment_document": 0,
            "labels": None,
        },
        {
            "flags": 10,
            "day": str(date.today() - timedelta(days=1)),
            "identities": 0,
            "traits": 0,
            "environment_document": 0,
            "labels": None,
        },
    ]

    mocked_get_usage_data.assert_called_once_with(
        organisation_id=organisation.id,
        environment_id=None,
        project_id=None,
        date_start=ninety_days_ago,
        date_stop=now,
        labels_filter=None,
    )


def test_get_usage_data__labels_filter__returns_expected(
    mocker: MockerFixture,
    admin_client_new: APIClient,
    organisation: Organisation,
) -> None:
    # Given
    today = date.today()

    url = reverse("api-v1:organisations:usage-data", args=[organisation.id])
    url += "?client_application_name=test-app"

    mocked_get_usage_data = mocker.patch(
        "app_analytics.views.get_usage_data",
        autospec=True,
        return_value=[
            UsageData(
                flags=10,
                day=today,
                labels={"client_application_name": "test-app"},
            ),
        ],
    )

    # When
    response = admin_client_new.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [
        {
            "flags": 10,
            "day": str(today),
            "identities": 0,
            "traits": 0,
            "environment_document": 0,
            "labels": {
                "client_application_name": "test-app",
                "client_application_version": None,
            },
        },
    ]

    mocked_get_usage_data.assert_called_once_with(
        organisation=organisation,
        period=None,
        labels_filter={"client_application_name": "test-app"},
    )


def test_get_usage_data_for_non_admin_user_returns_403(  # type: ignore[no-untyped-def]
    mocker, test_user_client, organisation
):
    # Given
    url = reverse("api-v1:organisations:usage-data", args=[organisation.id])

    # When
    response = test_user_client.get(url)

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_total_usage_count(mocker, admin_client, organisation):  # type: ignore[no-untyped-def]
    # Given
    url = reverse(
        "api-v1:organisations:usage-data-total-count",
        args=[organisation.id],
    )
    mocked_get_total_events_count = mocker.patch(
        "app_analytics.views.get_total_events_count",
        autospec=True,
        return_value=100,
    )

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"count": 100}
    mocked_get_total_events_count.assert_called_once_with(organisation)


def test_get_total_usage_count_for_non_admin_user_returns_403(  # type: ignore[no-untyped-def]
    mocker, test_user_client, organisation
):
    # Given
    url = reverse(
        "api-v1:organisations:usage-data-total-count",
        args=[organisation.id],
    )
    # When
    response = test_user_client.get(url)

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.skip_if_no_analytics_db
@pytest.mark.django_db(databases=["default", "analytics"])
def test_set_sdk_analytics_flags_with_identifier(
    api_client: APIClient,
    environment: Environment,
    feature: Feature,
    identity: Identity,
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.USE_POSTGRES_FOR_ANALYTICS = True
    url = reverse("api-v2:analytics-flags")
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)
    feature_request_count = 2

    data = {
        "evaluations": [
            {
                "feature_name": feature.name,
                "identity_identifier": identity.identifier,
                "count": feature_request_count,
                "enabled_when_evaluated": True,
            }
        ]
    }

    # When
    response = api_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT

    assert FeatureEvaluationRaw.objects.count() == 1
    feature_evaluation_raw = FeatureEvaluationRaw.objects.first()
    assert feature_evaluation_raw.identity_identifier == identity.identifier  # type: ignore[union-attr]
    assert feature_evaluation_raw.feature_name == feature.name  # type: ignore[union-attr]
    assert feature_evaluation_raw.environment_id == environment.id  # type: ignore[union-attr]
    assert feature_evaluation_raw.evaluation_count is feature_request_count  # type: ignore[union-attr]


@pytest.mark.skip_if_no_analytics_db
@pytest.mark.django_db(databases=["default", "analytics"])
def test_set_sdk_analytics_flags_without_identifier(
    api_client: APIClient,
    environment: Environment,
    feature: Feature,
    identity: Identity,
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.USE_POSTGRES_FOR_ANALYTICS = True
    url = reverse("api-v2:analytics-flags")
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)
    feature_request_count = 2
    data = {
        "evaluations": [
            {
                "feature_name": feature.name,
                "count": feature_request_count,
                "enabled_when_evaluated": True,
            },
            {
                "feature_name": "invalid_feature_name",
                "count": 10,
                "enabled_when_evaluated": True,
            },
        ]
    }

    # When
    response = api_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT

    assert FeatureEvaluationRaw.objects.count() == 1
    feature_evaluation_raw = FeatureEvaluationRaw.objects.first()
    assert feature_evaluation_raw.identity_identifier is None  # type: ignore[union-attr]
    assert feature_evaluation_raw.feature_name == feature.name  # type: ignore[union-attr]
    assert feature_evaluation_raw.environment_id == environment.id  # type: ignore[union-attr]
    assert feature_evaluation_raw.evaluation_count is feature_request_count  # type: ignore[union-attr]


def test_set_sdk_analytics_flags_with_identifier__influx__calls_expected(
    api_client: APIClient,
    environment: Environment,
    feature: Feature,
    identity: Identity,
    settings: SettingsWrapper,
    mocker: MockerFixture,
) -> None:
    # Given
    settings.INFLUXDB_TOKEN = "test-token"
    influx_db_wrapper_mock = mocker.patch(
        "app_analytics.track.InfluxDBWrapper",
        autospec=True,
    ).return_value

    url = reverse("api-v2:analytics-flags")
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)
    feature_request_count = 2

    data = {
        "evaluations": [
            {
                "feature_name": feature.name,
                "identity_identifier": identity.identifier,
                "count": feature_request_count,
                "enabled_when_evaluated": True,
            },
            {
                "feature_name": "invalid_feature_name",
                "identity_identifier": identity.identifier,
                "count": 10,
                "enabled_when_evaluated": True,
            },
        ]
    }

    # When
    response = api_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    influx_db_wrapper_mock.add_data_point.assert_called_once_with(
        "request_count",
        feature_request_count,
        tags={"feature_id": feature.name, "environment_id": environment.id},
    )
    influx_db_wrapper_mock.write.assert_called_once()


def test_sdk_analytics_flags_v1(
    api_client: APIClient,
    environment: Environment,
    feature: Feature,
    mocker: MockerFixture,
) -> None:
    # Given
    url = reverse("api-v1:analytics-flags")
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)
    feature_request_count = 2
    data = {feature.name: feature_request_count}

    mocked_feature_evaluation_cache = mocker.patch(
        "app_analytics.views.feature_evaluation_cache"
    )

    # When
    response = api_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    mocked_feature_evaluation_cache.track_feature_evaluation.assert_called_once_with(
        environment_id=environment.id,
        feature_name=feature.name,
        evaluation_count=feature_request_count,
        labels={},
    )
