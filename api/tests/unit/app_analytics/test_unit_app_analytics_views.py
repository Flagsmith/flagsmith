import json
from datetime import date, timedelta

import pytest
from app_analytics.dataclasses import UsageData
from app_analytics.models import FeatureEvaluationRaw
from app_analytics.views import SDKAnalyticsFlags
from django.conf import settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from environments.identities.models import Identity
from environments.models import Environment
from features.models import Feature


def test_sdk_analytics_does_not_allow_bad_data(mocker, settings, environment):
    # Given
    settings.INFLUXDB_TOKEN = "some-token"

    data = {"bad": "data"}
    request = mocker.MagicMock(data=data, environment=environment)

    view = SDKAnalyticsFlags(request=request)

    mocked_track_feature_eval = mocker.patch(
        "app_analytics.views.track_feature_evaluation_influxdb"
    )

    # When
    response = view.post(request)

    # Then
    assert response.status_code == status.HTTP_200_OK
    mocked_track_feature_eval.assert_not_called()


def test_sdk_analytics_allows_valid_data(mocker, settings, environment, feature):
    # Given
    settings.INFLUXDB_TOKEN = "some-token"

    data = {feature.name: 12}
    request = mocker.MagicMock(
        data=data,
        environment=environment,
        query_params={},
    )

    view = SDKAnalyticsFlags(request=request)

    mocked_track_feature_eval = mocker.patch(
        "app_analytics.views.track_feature_evaluation_influxdb"
    )

    # When
    response = view.post(request)

    # Then
    assert response.status_code == status.HTTP_200_OK
    mocked_track_feature_eval.assert_called_once_with(environment.id, data)


def test_get_usage_data(mocker, admin_client, organisation):
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
        },
        {
            "flags": 10,
            "day": str(date.today() - timedelta(days=1)),
            "identities": 0,
            "traits": 0,
            "environment_document": 0,
        },
    ]
    mocked_get_usage_data.assert_called_once_with(organisation)


def test_get_usage_data_for_non_admin_user_returns_403(
    mocker, test_user_client, organisation
):
    # Given
    url = reverse("api-v1:organisations:usage-data", args=[organisation.id])

    # When
    response = test_user_client.get(url)

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_total_usage_count(mocker, admin_client, organisation):
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


def test_get_total_usage_count_for_non_admin_user_returns_403(
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


@pytest.mark.skipif(
    "analytics" not in settings.DATABASES,
    reason="Skip test if analytics DB is not configured",
)
@pytest.mark.django_db(databases=["default", "analytics"])
def test_set_sdk_analytics_flags_with_identifier(
    api_client: APIClient,
    environment: Environment,
    feature: Feature,
    identity: Identity,
) -> None:
    # Given
    url = reverse("api-v1:analytics-flags")
    url += f"?identity_identifier={identity.identifier}"
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)
    feature_request_count = 2
    data = {feature.name: feature_request_count}

    # When
    response = api_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK

    FeatureEvaluationRaw.objects.count == 1
    feature_evaluation_raw = FeatureEvaluationRaw.objects.first()
    assert feature_evaluation_raw.identity_identifier == identity.identifier
    assert feature_evaluation_raw.feature_name == feature.name
    assert feature_evaluation_raw.environment_id == environment.id
    assert feature_evaluation_raw.evaluation_count == feature_request_count


@pytest.mark.skipif(
    "analytics" not in settings.DATABASES,
    reason="Skip test if analytics DB is not configured",
)
@pytest.mark.django_db(databases=["default", "analytics"])
def test_set_sdk_analytics_flags_with_enabled_when_evaluated(
    api_client: APIClient,
    environment: Environment,
    feature: Feature,
) -> None:
    # Given
    url = reverse("api-v1:analytics-flags")
    url += "?enabled_when_evaluated=true"
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)
    feature_request_count = 2
    data = {feature.name: feature_request_count}

    # When
    response = api_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK

    FeatureEvaluationRaw.objects.count == 1
    feature_evaluation_raw = FeatureEvaluationRaw.objects.first()
    assert feature_evaluation_raw.feature_name == feature.name
    assert feature_evaluation_raw.environment_id == environment.id
    assert feature_evaluation_raw.enabled_when_evaluated is True
