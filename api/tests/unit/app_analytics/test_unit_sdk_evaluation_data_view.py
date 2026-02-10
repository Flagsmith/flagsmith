import json
from datetime import datetime, timezone

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from environments.models import Environment
from features.models import Feature


def test_sdk_evaluation_data_view__valid_data__returns_202(
    api_client: APIClient,
    environment: Environment,
    feature: Feature,
) -> None:
    # Given
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)
    url = reverse("api-v2:analytics-evaluations")

    evaluation_timestamp = datetime.now(timezone.utc).isoformat()
    data = {
        "evaluations": [
            {
                "feature_name": feature.name,
                "enabled": True,
                "value": "test_value",
                "evaluation_timestamp": evaluation_timestamp,
                "identity_identifier": "test_identity",
                "identity_traits": [
                    {"trait_key": "email", "trait_value": "test@example.com"},
                    {"trait_key": "age", "trait_value": 25},
                ],
                "segment_names": ["segment1", "segment2"],
            }
        ]
    }

    # When
    response = api_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_202_ACCEPTED


def test_sdk_evaluation_data_view__multiple_evaluations__returns_202(
    api_client: APIClient,
    environment: Environment,
    feature: Feature,
) -> None:
    # Given
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)
    url = reverse("api-v2:analytics-evaluations")

    evaluation_timestamp = datetime.now(timezone.utc).isoformat()
    data = {
        "evaluations": [
            {
                "feature_name": feature.name,
                "enabled": True,
                "value": "value1",
                "evaluation_timestamp": evaluation_timestamp,
                "identity_identifier": "identity1",
                "identity_traits": [
                    {"trait_key": "email", "trait_value": "user1@example.com"}
                ],
                "segment_names": ["segment1"],
            },
            {
                "feature_name": feature.name,
                "enabled": False,
                "value": None,
                "evaluation_timestamp": evaluation_timestamp,
                "identity_identifier": "identity2",
                "identity_traits": [],
                "segment_names": [],
            },
        ]
    }

    # When
    response = api_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_202_ACCEPTED


def test_sdk_evaluation_data_view__minimal_data__returns_202(
    api_client: APIClient,
    environment: Environment,
    feature: Feature,
) -> None:
    # Given
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)
    url = reverse("api-v2:analytics-evaluations")

    evaluation_timestamp = datetime.now(timezone.utc).isoformat()
    data = {
        "evaluations": [
            {
                "feature_name": feature.name,
                "enabled": True,
                "evaluation_timestamp": evaluation_timestamp,
            }
        ]
    }

    # When
    response = api_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_202_ACCEPTED


def test_sdk_evaluation_data_view__invalid_feature_name__filters_out(
    api_client: APIClient,
    environment: Environment,
    feature: Feature,
) -> None:
    # Given
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)
    url = reverse("api-v2:analytics-evaluations")

    evaluation_timestamp = datetime.now(timezone.utc).isoformat()
    data = {
        "evaluations": [
            {
                "feature_name": "invalid_feature_name",
                "enabled": True,
                "evaluation_timestamp": evaluation_timestamp,
            },
            {
                "feature_name": feature.name,
                "enabled": True,
                "evaluation_timestamp": evaluation_timestamp,
            },
        ]
    }

    # When
    response = api_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_202_ACCEPTED


def test_sdk_evaluation_data_view__missing_required_field__returns_400(
    api_client: APIClient,
    environment: Environment,
) -> None:
    # Given
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)
    url = reverse("api-v2:analytics-evaluations")

    data = {
        "evaluations": [
            {
                "feature_name": "test_feature",
                # Missing 'enabled' field
                "evaluation_timestamp": datetime.now(timezone.utc).isoformat(),
            }
        ]
    }

    # When
    response = api_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_sdk_evaluation_data_view__no_environment_key__returns_403(
    api_client: APIClient,
    environment: Environment,
    feature: Feature,
) -> None:
    # Given
    url = reverse("api-v2:analytics-evaluations")

    evaluation_timestamp = datetime.now(timezone.utc).isoformat()
    data = {
        "evaluations": [
            {
                "feature_name": feature.name,
                "enabled": True,
                "evaluation_timestamp": evaluation_timestamp,
            }
        ]
    }

    # When
    response = api_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_sdk_evaluation_data_view__invalid_environment_key__returns_403(
    api_client: APIClient,
    environment: Environment,
    feature: Feature,
) -> None:
    # Given
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY="invalid_key")
    url = reverse("api-v2:analytics-evaluations")

    evaluation_timestamp = datetime.now(timezone.utc).isoformat()
    data = {
        "evaluations": [
            {
                "feature_name": feature.name,
                "enabled": True,
                "evaluation_timestamp": evaluation_timestamp,
            }
        ]
    }

    # When
    response = api_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_sdk_evaluation_data_view__empty_evaluations_list__returns_202(
    api_client: APIClient,
    environment: Environment,
) -> None:
    # Given
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)
    url = reverse("api-v2:analytics-evaluations")

    data: dict[str, list[dict[str, str]]] = {"evaluations": []}

    # When
    response = api_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_202_ACCEPTED


def test_sdk_evaluation_data_view__complex_trait_values__returns_202(
    api_client: APIClient,
    environment: Environment,
    feature: Feature,
) -> None:
    # Given
    api_client.credentials(HTTP_X_ENVIRONMENT_KEY=environment.api_key)
    url = reverse("api-v2:analytics-evaluations")

    evaluation_timestamp = datetime.now(timezone.utc).isoformat()
    data = {
        "evaluations": [
            {
                "feature_name": feature.name,
                "enabled": True,
                "value": {"nested": {"object": "value"}},
                "evaluation_timestamp": evaluation_timestamp,
                "identity_identifier": "test_identity",
                "identity_traits": [
                    {"trait_key": "email", "trait_value": "test@example.com"},
                    {"trait_key": "age", "trait_value": 25},
                    {"trait_key": "active", "trait_value": True},
                    {"trait_key": "score", "trait_value": 9.5},
                    {
                        "trait_key": "metadata",
                        "trait_value": {"country": "UK", "city": "London"},
                    },
                ],
                "segment_names": ["premium", "active_users"],
            }
        ]
    }

    # When
    response = api_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_202_ACCEPTED
