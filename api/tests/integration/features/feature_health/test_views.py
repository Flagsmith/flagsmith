import json
from datetime import datetime, timedelta

import pytest
from django.urls import reverse
from freezegun import freeze_time
from pytest_mock import MockerFixture
from rest_framework.test import APIClient

from tests.types import AdminClientAuthType


@pytest.fixture
def expected_created_by(
    admin_client_auth_type: AdminClientAuthType,
    admin_user_email: str,
) -> str | None:
    if admin_client_auth_type == "user":
        return admin_user_email
    return None


def test_feature_health_providers__get__expected_response(
    project: int,
    admin_client_new: APIClient,
    expected_created_by: str | None,
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
        "created_by": expected_created_by,
        "name": "Sample",
        "project": project,
        "webhook_url": mocker.ANY,
    }
    assert expected_feature_health_provider_data["webhook_url"].startswith(
        "http://testserver/api/v1/feature-health/"
    )
    assert response.status_code == 200
    assert response.json() == [expected_feature_health_provider_data]


def test_feature_health_providers__delete__expected_response(
    project: int,
    admin_client_new: APIClient,
) -> None:
    # Given
    url = reverse("api-v1:projects:feature-health-providers-list", args=[project])
    admin_client_new.post(
        url,
        data={"name": "Sample"},
    ).json()

    # When

    response = admin_client_new.delete(
        reverse(
            "api-v1:projects:feature-health-providers-detail",
            args=[project, "sample"],
        )
    )

    # Then
    assert response.status_code == 204
    response = admin_client_new.get(url)
    assert response.json() == []


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
            "reason": None,
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
            "reason": None,
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
            "reason": None,
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


def test_webhook__grafana_provider__post__expected_feature_health_event_created(
    project: int,
    feature: int,
    feature_name: str,
    grafana_feature_health_provider_webhook_url: str,
    api_client: APIClient,
    admin_client_new: APIClient,
) -> None:
    # Given
    feature_health_events_url = reverse(
        "api-v1:projects:feature-health-events-list", args=[project]
    )
    webhook_data = {
        "alerts": [
            {
                "status": "firing",
                "labels": {
                    "alertname": "Panel Title",
                    "flagsmith_feature": feature_name,
                    "grafana_folder": "Test",
                },
                "annotations": {
                    "description": "This is the description.",
                    "runbook_url": "https://hit.me",
                    "summary": "This is a summary.",
                },
                "startsAt": "2025-02-12T21:06:50Z",
                "endsAt": "0001-01-01T00:00:00Z",
                "generatorURL": "https://grafana.example.com/alerting/grafana/aebbhjnirottsa/view?orgId=1",
                "dashboardURL": "https://grafana.example.com/d/ce99ti2tuu3nka?orgId=1",
                "panelURL": "https://grafana.example.com/d/ce99ti2tuu3nka?orgId=1&viewPanel=1",
                "fingerprint": "e8790ab48f71f61e",
            }
        ],
    }
    expected_reason = {
        "text_blocks": [
            {"text": "This is the description.", "title": "Panel Title"},
            {"text": "This is a summary.", "title": "Summary"},
        ],
        "url_blocks": [
            {
                "title": "Alert",
                "url": "https://grafana.example.com/alerting/grafana/aebbhjnirottsa/view?orgId=1",
            },
            {
                "title": "Dashboard",
                "url": "https://grafana.example.com/d/ce99ti2tuu3nka?orgId=1",
            },
            {
                "title": "Panel",
                "url": "https://grafana.example.com/d/ce99ti2tuu3nka?orgId=1&viewPanel=1",
            },
            {"title": "Runbook", "url": "https://hit.me"},
        ],
    }

    # When
    response = api_client.post(
        grafana_feature_health_provider_webhook_url,
        data=json.dumps(webhook_data),
        content_type="application/json",
    )

    # Then
    assert response.status_code == 200
    response = admin_client_new.get(feature_health_events_url)
    assert response.json() == [
        {
            "created_at": "2025-02-12T21:06:50Z",
            "environment": None,
            "feature": feature,
            "provider_name": "Grafana",
            "reason": expected_reason,
            "type": "UNHEALTHY",
        }
    ]


def test_webhook__grafana_provider__post__multiple__expected_feature_health_events(
    project: int,
    environment: int,
    environment_name: str,
    feature: int,
    feature_name: str,
    grafana_feature_health_provider_webhook_url: str,
    api_client: APIClient,
    admin_client_new: APIClient,
) -> None:
    # Given
    feature_health_events_url = reverse(
        "api-v1:projects:feature-health-events-list", args=[project]
    )
    webhook_data = {
        "alerts": [
            {
                "status": "firing",
                "labels": {
                    "alertname": "Panel Title",
                    "flagsmith_feature": feature_name,
                    "grafana_folder": "Test",
                },
                "annotations": {
                    "description": "This is the description.",
                    "runbook_url": "https://hit.me",
                    "summary": "This is a summary.",
                },
                "startsAt": "2025-02-12T21:06:50Z",
                "endsAt": "0001-01-01T00:00:00Z",
                "generatorURL": "https://grafana.example.com/alerting/grafana/aebbhjnirottsa/view?orgId=1",
                "fingerprint": "e8790ab48f71f61e",
            }
        ],
    }
    expected_reason = {
        "text_blocks": [
            {"text": "This is the description.", "title": "Panel Title"},
            {"text": "This is a summary.", "title": "Summary"},
        ],
        "url_blocks": [
            {
                "title": "Alert",
                "url": "https://grafana.example.com/alerting/grafana/aebbhjnirottsa/view?orgId=1",
            },
            {"title": "Runbook", "url": "https://hit.me"},
        ],
    }
    other_webhook_data = {
        "alerts": [
            {
                "status": "firing",
                "labels": {
                    "alertname": "Other Panel Title",
                    "flagsmith_feature": feature_name,
                    "flagsmith_environment": environment_name,
                    "grafana_folder": "Test",
                },
                "annotations": {
                    "description": "This is the description.",
                    "summary": "This is a summary.",
                },
                "startsAt": "2025-02-12T21:07:50Z",
                "endsAt": "0001-01-01T00:00:00Z",
                "generatorURL": "https://grafana.example.com/alerting/grafana/xjshhbiigohd/view?orgId=1",
                "fingerprint": "ba6b7c8d9e0f1",
            }
        ],
    }
    expected_other_reason = {
        "text_blocks": [
            {"text": "This is the description.", "title": "Other Panel Title"},
            {"text": "This is a summary.", "title": "Summary"},
        ],
        "url_blocks": [
            {
                "title": "Alert",
                "url": "https://grafana.example.com/alerting/grafana/xjshhbiigohd/view?orgId=1",
            }
        ],
    }
    unrelated_webhook_data = {
        "alerts": [
            {
                "status": "firing",
                "labels": {
                    "alertname": "Different",
                    "grafana_folder": "Test",
                },
                "annotations": {
                    "description": "This is the description.",
                    "runbook_url": "https://hit.me",
                    "summary": "This is a summary.",
                },
                "startsAt": "2025-02-12T21:08:50Z",
                "endsAt": "0001-01-01T00:00:00Z",
                "generatorURL": "https://grafana.example.com/alerting/grafana/aebbhjnirottsa/view?orgId=1",
                "fingerprint": "a6b7c8d9e0f1",
            }
        ],
    }
    resolved_webhook_data = {
        "alerts": [
            {
                "status": "resolved",
                "labels": {
                    "alertname": "Panel Title",
                    "flagsmith_feature": feature_name,
                    "grafana_folder": "Test",
                },
                "annotations": {
                    "description": "This is the description.",
                    "runbook_url": "https://hit.me",
                    "summary": "This is a summary.",
                },
                "startsAt": "2025-02-12T21:10:50Z",
                "endsAt": "2025-02-12T21:12:50Z",
                "generatorURL": "https://grafana.example.com/alerting/grafana/aebbhjnirottsa/view?orgId=1",
                "fingerprint": "e8790ab48f71f61e",
            }
        ],
    }

    # When
    # webhook is triggered by a firing alert...
    api_client.post(
        grafana_feature_health_provider_webhook_url,
        data=json.dumps(webhook_data),
        content_type="application/json",
    )
    # ...webhook triggered by a resolved alert that previously fired...
    api_client.post(
        grafana_feature_health_provider_webhook_url,
        data=json.dumps(resolved_webhook_data),
        content_type="application/json",
    )
    # ...webhook triggered by a firing alert that is unrelated to the first and has an environment label...
    api_client.post(
        grafana_feature_health_provider_webhook_url,
        data=json.dumps(other_webhook_data),
        content_type="application/json",
    )
    # ...webhook triggered by a firing alert that is unrelated to the feature.
    response = api_client.post(
        grafana_feature_health_provider_webhook_url,
        data=json.dumps(unrelated_webhook_data),
        content_type="application/json",
    )

    # Then
    # unrelated alert was not accepted by webhook
    assert response.status_code == 400
    response = admin_client_new.get(feature_health_events_url)
    assert response.json() == [
        # second firing alert has not been resolved
        # and provided an environment label
        {
            "created_at": "2025-02-12T21:07:50Z",
            "environment": environment,
            "feature": feature,
            "provider_name": "Grafana",
            "reason": expected_other_reason,
            "type": "UNHEALTHY",
        },
        # first firing alert has been resolved
        {
            "created_at": "2025-02-12T21:12:50Z",
            "environment": None,
            "feature": feature,
            "provider_name": "Grafana",
            "reason": expected_reason,
            "type": "HEALTHY",
        },
    ]
