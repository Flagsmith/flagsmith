import pytest
from pytest_structlog import StructuredLogCapture
from rest_framework.test import APIClient

from environments.models import Environment
from features.dependencies.models import SegmentFlagReference
from features.dependencies.types import DependencyEdge
from features.models import Feature

pytestmark = pytest.mark.usefixtures("versioned_environment")


def test_delete_feature__feature_has_prerequisite__deletion_goes_through(
    admin_client: APIClient,
    environment_api_key: str,
    log: StructuredLogCapture,
    organisation: int,
    project: int,
) -> None:
    # Given
    feature = Feature.objects.create(name="checkout", project_id=project)
    prerequisite = Feature.objects.create(name="payments", project_id=project)
    admin_client.post(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/{prerequisite.id}/",
    )

    # When
    response = admin_client.delete(
        f"/api/v1/projects/{project}/features/{feature.id}/",
    )

    # Then
    assert response.status_code == 204
    assert not SegmentFlagReference.objects.exists()
    assert log.has(
        "dependencies.deleted",
        level="info",
        organisation__id=organisation,
        project__id=project,
        environment__key=environment_api_key,
        feature__name="checkout",
        prerequisite_feature__name="payments",
    )


def test_delete_feature__feature_is_prerequisite__deletion_rejected(
    admin_client: APIClient,
    environment_api_key: str,
    environment_name: str,
    project: int,
) -> None:
    # Given
    feature = Feature.objects.create(name="checkout", project_id=project)
    prerequisite = Feature.objects.create(name="payments", project_id=project)
    segment_id = admin_client.post(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/{prerequisite.id}/",
    ).json()["segment"]["id"]

    # When
    response = admin_client.delete(
        f"/api/v1/projects/{project}/features/{prerequisite.id}/",
    )

    # Then
    assert response.status_code == 400
    assert response.json() == {
        "code": "feature_is_prerequisite",
        "message": 'The feature "payments" is a prerequisite for the feature "checkout".',
        "environment": {"key": environment_api_key, "name": environment_name},
        "path": [
            DependencyEdge(
                {
                    "feature": {"id": feature.id, "name": "checkout"},
                    "prerequisite": {"id": prerequisite.id, "name": "payments"},
                    "segment": {
                        "id": segment_id,
                        "name": "checkout-depends-on-payments",
                        "rules": [
                            {
                                "type": "ANY",
                                "conditions": [
                                    {
                                        "property": '$.flags["payments"].enabled',
                                        "operator": "NOT_EQUAL",
                                        "value": "true",
                                        "description": None,
                                    }
                                ],
                                "rules": [],
                            }
                        ],
                        "condition_json_path": "$[0].conditions[0]",
                        "is_system": True,
                    },
                }
            )
        ],
    }
    assert Feature.objects.filter(id=prerequisite.id).exists()
    assert list(
        SegmentFlagReference.objects.values(
            "segment", "prerequisite_feature", "condition_json_path"
        )
    ) == [
        {
            "segment": segment_id,
            "prerequisite_feature": prerequisite.id,
            "condition_json_path": "$[0].conditions[0]",
        }
    ]


def test_delete_feature__feature_referenced_in_user_segment_without_overrides__deletion_rejected(
    admin_client: APIClient,
    project: int,
) -> None:
    # Given
    prerequisite = Feature.objects.create(name="payments", project_id=project)
    segment_id = admin_client.post(
        f"/api/v1/projects/{project}/segments/",
        data={
            "name": "needs_payments",
            "rules": (
                needs_payments := [
                    {
                        "type": "ALL",
                        "conditions": [
                            {
                                "property": "$.flags.payments.enabled",
                                "operator": "EQUAL",
                                "value": "true",
                                "description": None,
                            }
                        ],
                        "rules": [],
                    }
                ]
            ),
        },
        format="json",
    ).json()["id"]

    # When
    response = admin_client.delete(
        f"/api/v1/projects/{project}/features/{prerequisite.id}/",
    )

    # Then
    assert response.status_code == 400
    assert response.json() == {
        "code": "feature_is_referenced",
        "message": 'The segment "needs_payments" references the feature "payments".',
        "segments": [
            {
                "id": segment_id,
                "name": "needs_payments",
                "rules": needs_payments,
                "condition_json_path": "$[0].conditions[0]",
                "is_system": False,
            }
        ],
    }
    assert Feature.objects.filter(id=prerequisite.id).exists()
    assert list(
        SegmentFlagReference.objects.values(
            "segment", "prerequisite_feature", "condition_json_path"
        )
    ) == [
        {
            "segment": segment_id,
            "prerequisite_feature": prerequisite.id,
            "condition_json_path": "$[0].conditions[0]",
        }
    ]


def test_delete_feature__feature_is_prerequisite_in_another_environment__deletion_rejected(
    admin_client: APIClient,
    other_environment: Environment,
    project: int,
) -> None:
    # Given
    feature = Feature.objects.create(name="checkout", project_id=project)
    prerequisite = Feature.objects.create(name="payments", project_id=project)
    segment_id = admin_client.post(
        f"/api/v1/environments/{other_environment.api_key}/features/{feature.id}/dependencies/{prerequisite.id}/",
    ).json()["segment"]["id"]

    # When
    response = admin_client.delete(
        f"/api/v1/projects/{project}/features/{prerequisite.id}/",
    )

    # Then
    assert response.status_code == 400
    assert response.json() == {
        "code": "feature_is_prerequisite",
        "message": 'The feature "payments" is a prerequisite for the feature "checkout".',
        "environment": {
            "key": other_environment.api_key,
            "name": other_environment.name,
        },
        "path": [
            DependencyEdge(
                {
                    "feature": {"id": feature.id, "name": "checkout"},
                    "prerequisite": {"id": prerequisite.id, "name": "payments"},
                    "segment": {
                        "id": segment_id,
                        "name": "checkout-depends-on-payments",
                        "rules": [
                            {
                                "type": "ANY",
                                "conditions": [
                                    {
                                        "property": '$.flags["payments"].enabled',
                                        "operator": "NOT_EQUAL",
                                        "value": "true",
                                        "description": None,
                                    }
                                ],
                                "rules": [],
                            }
                        ],
                        "condition_json_path": "$[0].conditions[0]",
                        "is_system": True,
                    },
                }
            )
        ],
    }
    assert Feature.objects.filter(id=prerequisite.id).exists()


def test_delete_feature__feature_removed_as_prerequisite__deletion_goes_through(
    admin_client: APIClient,
    environment_api_key: str,
    project: int,
) -> None:
    # Given
    feature = Feature.objects.create(name="checkout", project_id=project)
    prerequisite = Feature.objects.create(name="payments", project_id=project)
    admin_client.post(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/{prerequisite.id}/",
    )
    admin_client.delete(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/{prerequisite.id}/",
    )

    # When
    response = admin_client.delete(
        f"/api/v1/projects/{project}/features/{prerequisite.id}/",
    )

    # Then
    assert response.status_code == 204
    assert not Feature.objects.filter(id=prerequisite.id).exists()
    assert not SegmentFlagReference.objects.exists()
