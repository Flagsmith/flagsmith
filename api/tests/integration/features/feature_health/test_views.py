import json
from datetime import datetime, timedelta

import pytest
from django.urls import reverse
from freezegun import freeze_time
from pytest_mock import MockerFixture
from rest_framework.test import APIClient


def test_feature_health_providers__get__expected_response(
    project: int,
    admin_client_new: APIClient,
    admin_user_email: str,
    mocker: MockerFixture,
) -> None:
    # Given
    url = reverse("api-v1:projects:feature-health-providers-list", args=[project])
    expected_feature_health_provider_data = admin_client_new.post(
        url,
        data={"name": "Sample"},
    ).json()

    # When
    response = admin_client_new.get(url)

    # Then
    assert expected_feature_health_provider_data == {
        "created_by": admin_user_email,
        "name": "Sample",
        "project": project,
        "webhook_url": mocker.ANY,
    }
    assert expected_feature_health_provider_data["webhook_url"].startswith(
        "http://testserver/api/v1/feature-health/"
    )
    assert response.status_code == 200
    assert response.json() == [expected_feature_health_provider_data]


def test_webhook__invalid_path__expected_response(
    api_client: APIClient,
) -> None:
    # Given
    webhook_url = reverse("api-v1:feature-health-webhook", args=["invalid"])

    # When
    response = api_client.post(webhook_url)

    # Then
    assert response.status_code == 404


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_webhook__sample_provider__post__expected_feature_health_event_created__expected_tag_added(
    feature: int,
    project: int,
    feature_name: str,
    sample_feature_health_provider_webhook_url: str,
    api_client: APIClient,
    admin_client_new: APIClient,
) -> None:
    # Given
    feature_health_events_url = reverse(
        "api-v1:projects:feature-health-events-list", args=[project]
    )
    tags_url = reverse("api-v1:projects:tags-list", args=[project])
    features_url = reverse("api-v1:projects:project-features-list", args=[project])

    # When
    webhook_data = {
        "feature": feature_name,
        "status": "unhealthy",
    }
    response = api_client.post(
        sample_feature_health_provider_webhook_url,
        data=json.dumps(webhook_data),
        content_type="application/json",
    )

    # Then
    assert response.status_code == 200
    response = admin_client_new.get(feature_health_events_url)
    assert response.json() == [
        {
            "created_at": "2023-01-19T09:09:47.325132Z",
            "environment": None,
            "feature": feature,
            "provider_name": "Sample",
            "reason": "",
            "type": "UNHEALTHY",
        }
    ]
    response = admin_client_new.get(tags_url)
    assert (
        tag_data := next(
            tag_data
            for tag_data in response.json()["results"]
            if tag_data.get("label") == "Unhealthy"
        )
    )
    response = admin_client_new.get(features_url)
    feature_data = next(
        feature_data
        for feature_data in response.json()["results"]
        if feature_data.get("id") == feature
    )
    assert tag_data["id"] in feature_data["tags"]


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_webhook__sample_provider__post_with_environment_expected_feature_health_event_created(
    feature: int,
    project: int,
    environment: int,
    feature_name: str,
    environment_name: str,
    sample_feature_health_provider_webhook_url: str,
    api_client: APIClient,
    admin_client_new: APIClient,
) -> None:
    # Given
    feature_health_events_url = reverse(
        "api-v1:projects:feature-health-events-list", args=[project]
    )

    # When
    webhook_data = {
        "feature": feature_name,
        "environment": environment_name,
        "status": "unhealthy",
    }
    response = api_client.post(
        sample_feature_health_provider_webhook_url,
        data=json.dumps(webhook_data),
        content_type="application/json",
    )

    # Then
    assert response.status_code == 200
    response = admin_client_new.get(feature_health_events_url)
    assert response.json() == [
        {
            "created_at": "2023-01-19T09:09:47.325132Z",
            "environment": environment,
            "feature": feature,
            "provider_name": "Sample",
            "reason": "",
            "type": "UNHEALTHY",
        }
    ]


@pytest.mark.freeze_time("2023-01-19T09:09:47.325132+00:00")
def test_webhook__unhealthy_feature__post__expected_feature_health_event_created__expected_tag_removed(
    unhealthy_feature: int,
    project: int,
    feature_name: str,
    sample_feature_health_provider_webhook_url: str,
    api_client: APIClient,
    admin_client_new: APIClient,
) -> None:
    # Given
    feature_health_events_url = reverse(
        "api-v1:projects:feature-health-events-list", args=[project]
    )
    tags_url = reverse("api-v1:projects:tags-list", args=[project])
    features_url = reverse("api-v1:projects:project-features-list", args=[project])

    # When
    webhook_data = {
        "feature": feature_name,
        "status": "healthy",
    }
    with freeze_time(datetime.now() + timedelta(seconds=1)):
        response = api_client.post(
            sample_feature_health_provider_webhook_url,
            data=json.dumps(webhook_data),
            content_type="application/json",
        )

    # Then
    assert response.status_code == 200
    response = admin_client_new.get(feature_health_events_url)
    assert response.json() == [
        {
            "created_at": "2023-01-19T09:09:48.325132Z",
            "environment": None,
            "feature": unhealthy_feature,
            "provider_name": "Sample",
            "reason": "",
            "type": "HEALTHY",
        }
    ]
    response = admin_client_new.get(tags_url)
    assert (
        tag_data := next(
            tag_data
            for tag_data in response.json()["results"]
            if tag_data.get("label") == "Unhealthy"
        )
    )
    response = admin_client_new.get(features_url)
    feature_data = next(
        feature_data
        for feature_data in response.json()["results"]
        if feature_data.get("id") == unhealthy_feature
    )
    assert tag_data["id"] not in feature_data["tags"]


@pytest.mark.parametrize(
    "body", ["invalid", json.dumps({"status": "unhealthy", "feature": "non_existent"})]
)
def test_webhook__sample_provider__post__invalid_payload__expected_response(
    sample_feature_health_provider_webhook_url: str,
    api_client: APIClient,
    body: str,
) -> None:
    # When
    response = api_client.post(
        sample_feature_health_provider_webhook_url,
        data=body,
        content_type="application/json",
    )

    # Then
    assert response.status_code == 400
