import pytest
from common.environments.permissions import UPDATE_FEATURE_STATE
from pytest_structlog import StructuredLogCapture
from rest_framework.test import APIClient

from audit.models import AuditLog
from features.dependencies.models import SegmentFlagReference
from features.dependencies.types import DependencyEdge
from features.models import Feature
from organisations.models import Organisation
from segments.models import Segment
from tests.types import (
    CreateSegmentOverrideFixture,
    WithEnvironmentPermissionsCallable,
)
from users.models import FFAdminUser

pytestmark = pytest.mark.usefixtures("versioned_environment")


def test_add_feature_dependency__valid_prerequisite__responds_201_with_dependency(
    admin_client: APIClient,
    environment_api_key: str,
    log: StructuredLogCapture,
    organisation: int,
    project: int,
) -> None:
    # Given
    feature = Feature.objects.create(name="checkout", project_id=project)
    prerequisite = Feature.objects.create(name="payments", project_id=project)

    # When
    response = admin_client.post(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/{prerequisite.id}/",
    )

    # Then
    assert response.status_code == 201
    segment = Segment.objects.get(feature=feature, is_system_segment=True)
    assert response.json() == DependencyEdge(
        {
            "feature": {"id": feature.id, "name": "checkout"},
            "prerequisite": {"id": prerequisite.id, "name": "payments"},
            "segment": {
                "id": segment.id,
                "name": f"checkout-dependencies-{environment_api_key}",
                "rules": [
                    {
                        "type": "ANY",
                        "conditions": [
                            {
                                "property": "$.flags.payments.enabled",
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
    assert list(
        SegmentFlagReference.objects.values(
            "segment", "prerequisite_feature", "condition_json_path"
        )
    ) == [
        {
            "segment": segment.id,
            "prerequisite_feature": prerequisite.id,
            "condition_json_path": "$[0].conditions[0]",
        }
    ]
    flag_response = admin_client.get(
        f"/api/__future__/environments/{environment_api_key}/features/{feature.id}/",
    )
    assert flag_response.json()["segment_overrides"] == [
        {
            "segment": {"id": segment.id},
            "priority": 0,
            "enabled": False,
            "value": None,
            "variants": [],
        }
    ]
    assert list(
        AuditLog.objects.filter(related_object_type="FEATURE").values(
            "environment__api_key", "related_object_id", "log"
        )
    ) == [
        {
            "environment__api_key": environment_api_key,
            "related_object_id": feature.id,
            "log": "Feature 'payments' added as a dependency for feature 'checkout'.",
        }
    ]
    assert log.has(
        "dependencies.created",
        level="info",
        organisation__id=organisation,
        project__id=project,
        environment__key=environment_api_key,
        feature__name="checkout",
        prerequisite_feature__name="payments",
    )


def test_add_feature_dependency__feature_has_another_prerequisite__responds_201_reusing_segment(
    admin_client: APIClient,
    environment_api_key: str,
    log: StructuredLogCapture,
    organisation: int,
    project: int,
) -> None:
    # Given
    feature = Feature.objects.create(name="checkout", project_id=project)
    prerequisite = Feature.objects.create(name="payments", project_id=project)
    other_prerequisite = Feature.objects.create(name="inventory", project_id=project)
    segment_id = admin_client.post(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/{prerequisite.id}/",
    ).json()["segment"]["id"]

    # When
    response = admin_client.post(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/{other_prerequisite.id}/",
    )

    # Then
    assert response.status_code == 201
    segment = Segment.live_objects.get(feature=feature, is_system_segment=True)
    assert segment.id == segment_id
    assert response.json() == DependencyEdge(
        {
            "feature": {"id": feature.id, "name": "checkout"},
            "prerequisite": {"id": other_prerequisite.id, "name": "inventory"},
            "segment": {
                "id": segment.id,
                "name": f"checkout-dependencies-{environment_api_key}",
                "rules": [
                    {
                        "type": "ANY",
                        "conditions": [
                            {
                                "property": "$.flags.payments.enabled",
                                "operator": "NOT_EQUAL",
                                "value": "true",
                                "description": None,
                            },
                            {
                                "property": "$.flags.inventory.enabled",
                                "operator": "NOT_EQUAL",
                                "value": "true",
                                "description": None,
                            },
                        ],
                        "rules": [],
                    }
                ],
                "condition_json_path": "$[0].conditions[1]",
                "is_system": True,
            },
        }
    )
    assert list(
        SegmentFlagReference.objects.order_by("condition_json_path").values(
            "segment", "prerequisite_feature", "condition_json_path"
        )
    ) == [
        {
            "segment": segment.id,
            "prerequisite_feature": prerequisite.id,
            "condition_json_path": "$[0].conditions[0]",
        },
        {
            "segment": segment.id,
            "prerequisite_feature": other_prerequisite.id,
            "condition_json_path": "$[0].conditions[1]",
        },
    ]
    flag_response = admin_client.get(
        f"/api/__future__/environments/{environment_api_key}/features/{feature.id}/",
    )
    assert flag_response.json()["segment_overrides"] == [
        {
            "segment": {"id": segment.id},
            "priority": 0,
            "enabled": False,
            "value": None,
            "variants": [],
        }
    ]
    assert list(
        AuditLog.objects.filter(related_object_type="FEATURE").values(
            "environment__api_key", "related_object_id", "log"
        )
    ) == [
        {
            "environment__api_key": environment_api_key,
            "related_object_id": feature.id,
            "log": "Feature 'inventory' added as a dependency for feature 'checkout'.",
        },
        {
            "environment__api_key": environment_api_key,
            "related_object_id": feature.id,
            "log": "Feature 'payments' added as a dependency for feature 'checkout'.",
        },
    ]
    assert log.has(
        "dependencies.created",
        level="info",
        organisation__id=organisation,
        project__id=project,
        environment__key=environment_api_key,
        feature__name="checkout",
        prerequisite_feature__name="inventory",
    )


def test_add_feature_dependency__feature_has_another_override__responds_201_reordering_priorities(
    admin_client: APIClient,
    create_segment_override: CreateSegmentOverrideFixture,
    environment_api_key: str,
    log: StructuredLogCapture,
    organisation: int,
    project: int,
    segment: int,
) -> None:
    # Given
    feature = Feature.objects.create(name="checkout", project_id=project)
    prerequisite = Feature.objects.create(name="payments", project_id=project)
    create_segment_override(
        environment_api_key=environment_api_key,
        feature_id=feature.id,
        segment_id=segment,
        enabled=True,
        priority=0,
    )

    # When
    response = admin_client.post(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/{prerequisite.id}/",
    )

    # Then
    assert response.status_code == 201
    system_segment = Segment.objects.get(feature=feature, is_system_segment=True)
    assert response.json() == DependencyEdge(
        {
            "feature": {"id": feature.id, "name": "checkout"},
            "prerequisite": {"id": prerequisite.id, "name": "payments"},
            "segment": {
                "id": system_segment.id,
                "name": f"checkout-dependencies-{environment_api_key}",
                "rules": [
                    {
                        "type": "ANY",
                        "conditions": [
                            {
                                "property": "$.flags.payments.enabled",
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
    assert list(
        SegmentFlagReference.objects.values(
            "segment", "prerequisite_feature", "condition_json_path"
        )
    ) == [
        {
            "segment": system_segment.id,
            "prerequisite_feature": prerequisite.id,
            "condition_json_path": "$[0].conditions[0]",
        }
    ]
    flag_response = admin_client.get(
        f"/api/__future__/environments/{environment_api_key}/features/{feature.id}/",
    )
    assert flag_response.json()["segment_overrides"] == [
        {
            "segment": {"id": system_segment.id},
            "priority": 0,
            "enabled": False,
            "value": None,
            "variants": [],
        },
        {
            "segment": {"id": segment},
            "priority": 1,
            "enabled": True,
            "value": None,
            "variants": [],
        },
    ]
    assert list(
        AuditLog.objects.filter(related_object_type="FEATURE").values(
            "environment__api_key", "related_object_id", "log"
        )
    ) == [
        {
            "environment__api_key": environment_api_key,
            "related_object_id": feature.id,
            "log": "Feature 'payments' added as a dependency for feature 'checkout'.",
        }
    ]
    assert log.has(
        "dependencies.created",
        level="info",
        organisation__id=organisation,
        project__id=project,
        environment__key=environment_api_key,
        feature__name="checkout",
        prerequisite_feature__name="payments",
    )


def test_add_feature_dependency__prerequisite_already_has_prerequisite__responds_400_with_error(
    admin_client: APIClient,
    environment_api_key: str,
    environment_name: str,
    log: StructuredLogCapture,
    organisation: int,
    project: int,
) -> None:
    # Given
    feature = Feature.objects.create(name="checkout", project_id=project)
    prerequisite = Feature.objects.create(name="payments", project_id=project)
    prerequisite_of_prerequisite = Feature.objects.create(
        name="inventory", project_id=project
    )
    prerequisite_segment_id = admin_client.post(
        f"/api/v1/environments/{environment_api_key}/features/{prerequisite.id}/dependencies/{prerequisite_of_prerequisite.id}/",
    ).json()["segment"]["id"]

    # When
    response = admin_client.post(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/{prerequisite.id}/",
    )

    # Then
    assert response.status_code == 400
    prerequisite_segment = Segment.objects.get(id=prerequisite_segment_id)
    assert response.json() == {
        "code": "prerequisite_has_prerequisite",
        "message": 'The prerequisite "payments" already has a prerequisite "inventory".',
        "environment": {"key": environment_api_key, "name": environment_name},
        "path": [
            DependencyEdge(
                {
                    "feature": {"id": prerequisite.id, "name": "payments"},
                    "prerequisite": {
                        "id": prerequisite_of_prerequisite.id,
                        "name": "inventory",
                    },
                    "segment": {
                        "id": prerequisite_segment.id,
                        "name": f"payments-dependencies-{environment_api_key}",
                        "rules": [
                            {
                                "type": "ANY",
                                "conditions": [
                                    {
                                        "property": "$.flags.inventory.enabled",
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
    assert not Segment.objects.filter(feature=feature).exists()
    assert list(
        SegmentFlagReference.objects.values(
            "segment", "prerequisite_feature", "condition_json_path"
        )
    ) == [
        {
            "segment": prerequisite_segment.id,
            "prerequisite_feature": prerequisite_of_prerequisite.id,
            "condition_json_path": "$[0].conditions[0]",
        }
    ]
    flag_response = admin_client.get(
        f"/api/__future__/environments/{environment_api_key}/features/{feature.id}/",
    )
    assert flag_response.json()["segment_overrides"] == []
    assert list(
        AuditLog.objects.filter(related_object_type="FEATURE").values(
            "environment__api_key", "related_object_id", "log"
        )
    ) == [
        {
            "environment__api_key": environment_api_key,
            "related_object_id": prerequisite.id,
            "log": "Feature 'inventory' added as a dependency for feature 'payments'.",
        }
    ]
    assert log.has(
        "dependencies.create_failed",
        level="info",
        organisation__id=organisation,
        project__id=project,
        environment__key=environment_api_key,
        feature__name="checkout",
        prerequisite_feature__name="payments",
    )


def test_add_feature_dependency__feature_is_already_a_prerequisite__responds_400_with_error(
    admin_client: APIClient,
    environment_api_key: str,
    environment_name: str,
    log: StructuredLogCapture,
    organisation: int,
    project: int,
) -> None:
    # Given
    feature = Feature.objects.create(name="checkout", project_id=project)
    prerequisite = Feature.objects.create(name="payments", project_id=project)
    dependent = Feature.objects.create(name="storefront", project_id=project)
    dependent_segment_id = admin_client.post(
        f"/api/v1/environments/{environment_api_key}/features/{dependent.id}/dependencies/{feature.id}/",
    ).json()["segment"]["id"]

    # When
    response = admin_client.post(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/{prerequisite.id}/",
    )

    # Then
    assert response.status_code == 400
    dependent_segment = Segment.objects.get(id=dependent_segment_id)
    assert response.json() == {
        "code": "feature_is_prerequisite",
        "message": 'The feature "checkout" is already a prerequisite for the feature "storefront".',
        "environment": {"key": environment_api_key, "name": environment_name},
        "path": [
            DependencyEdge(
                {
                    "feature": {"id": dependent.id, "name": "storefront"},
                    "prerequisite": {"id": feature.id, "name": "checkout"},
                    "segment": {
                        "id": dependent_segment.id,
                        "name": f"storefront-dependencies-{environment_api_key}",
                        "rules": [
                            {
                                "type": "ANY",
                                "conditions": [
                                    {
                                        "property": "$.flags.checkout.enabled",
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
    assert not Segment.objects.filter(feature=feature).exists()
    assert list(
        SegmentFlagReference.objects.values(
            "segment", "prerequisite_feature", "condition_json_path"
        )
    ) == [
        {
            "segment": dependent_segment.id,
            "prerequisite_feature": feature.id,
            "condition_json_path": "$[0].conditions[0]",
        }
    ]
    flag_response = admin_client.get(
        f"/api/__future__/environments/{environment_api_key}/features/{feature.id}/",
    )
    assert flag_response.json()["segment_overrides"] == []
    assert list(
        AuditLog.objects.filter(related_object_type="FEATURE").values(
            "environment__api_key", "related_object_id", "log"
        )
    ) == [
        {
            "environment__api_key": environment_api_key,
            "related_object_id": dependent.id,
            "log": "Feature 'checkout' added as a dependency for feature 'storefront'.",
        }
    ]
    assert log.has(
        "dependencies.create_failed",
        level="info",
        organisation__id=organisation,
        project__id=project,
        environment__key=environment_api_key,
        feature__name="checkout",
        prerequisite_feature__name="payments",
    )


def test_add_feature_dependency__dependency_already_exists__responds_400_with_error(
    admin_client: APIClient,
    environment_api_key: str,
    environment_name: str,
    log: StructuredLogCapture,
    organisation: int,
    project: int,
) -> None:
    # Given
    feature = Feature.objects.create(name="checkout", project_id=project)
    prerequisite = Feature.objects.create(name="payments", project_id=project)
    segment_id = admin_client.post(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/{prerequisite.id}/",
    ).json()["segment"]["id"]

    # When
    response = admin_client.post(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/{prerequisite.id}/",
    )

    # Then
    assert response.status_code == 400
    segment = Segment.live_objects.get(feature=feature, is_system_segment=True)
    assert segment.id == segment_id
    assert response.json() == {
        "code": "dependency_exists",
        "message": 'The feature "checkout" already depends on the feature "payments".',
        "environment": {"key": environment_api_key, "name": environment_name},
        "path": [
            DependencyEdge(
                {
                    "feature": {"id": feature.id, "name": "checkout"},
                    "prerequisite": {"id": prerequisite.id, "name": "payments"},
                    "segment": {
                        "id": segment.id,
                        "name": f"checkout-dependencies-{environment_api_key}",
                        "rules": [
                            {
                                "type": "ANY",
                                "conditions": [
                                    {
                                        "property": "$.flags.payments.enabled",
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
    assert list(
        SegmentFlagReference.objects.values(
            "segment", "prerequisite_feature", "condition_json_path"
        )
    ) == [
        {
            "segment": segment.id,
            "prerequisite_feature": prerequisite.id,
            "condition_json_path": "$[0].conditions[0]",
        }
    ]
    assert list(
        AuditLog.objects.filter(related_object_type="FEATURE").values(
            "environment__api_key", "related_object_id", "log"
        )
    ) == [
        {
            "environment__api_key": environment_api_key,
            "related_object_id": feature.id,
            "log": "Feature 'payments' added as a dependency for feature 'checkout'.",
        }
    ]
    assert log.has(
        "dependencies.create_failed",
        level="info",
        organisation__id=organisation,
        project__id=project,
        environment__key=environment_api_key,
        feature__name="checkout",
        prerequisite_feature__name="payments",
    )


def test_add_feature_dependency__prerequisite_is_self__responds_400_with_error(
    admin_client: APIClient,
    environment_api_key: str,
    log: StructuredLogCapture,
    organisation: int,
    project: int,
) -> None:
    # Given
    feature = Feature.objects.create(name="checkout", project_id=project)

    # When
    response = admin_client.post(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/{feature.id}/",
    )

    # Then
    assert response.status_code == 400
    assert response.json() == {
        "code": "prerequisite_is_self",
        "message": "A feature cannot depend on itself.",
    }
    assert not Segment.objects.filter(feature=feature).exists()
    assert not SegmentFlagReference.objects.exists()
    flag_response = admin_client.get(
        f"/api/__future__/environments/{environment_api_key}/features/{feature.id}/",
    )
    assert flag_response.json()["segment_overrides"] == []
    assert list(AuditLog.objects.filter(related_object_type="FEATURE")) == []
    assert log.has(
        "dependencies.create_failed",
        level="info",
        organisation__id=organisation,
        project__id=project,
        environment__key=environment_api_key,
        feature__name="checkout",
        prerequisite_feature__name="checkout",
    )


@pytest.mark.parametrize(
    "url, message",
    [  # Have you reset your test database today? 👀
        pytest.param(
            "/api/v1/environments/{environment_api_key}/features/777333777/dependencies/{prerequisite_feature_id}/",
            "Feature ID '777333777' does not exist in the project.",
            id="feature",
        ),
        pytest.param(
            "/api/v1/environments/{environment_api_key}/features/{feature_id}/dependencies/333777333/",
            "Feature ID '333777333' does not exist in the project.",
            id="prerequisite_feature",
        ),
    ],
)
def test_add_feature_dependency__either_feature_does_not_exist__responds_404_with_error(
    admin_client: APIClient,
    environment_api_key: str,
    log: StructuredLogCapture,
    message: str,
    project: int,
    url: str,
) -> None:
    # Given
    feature = Feature.objects.create(name="checkout", project_id=project)
    prerequisite = Feature.objects.create(name="payments", project_id=project)

    # When
    response = admin_client.post(
        url.format(
            environment_api_key=environment_api_key,
            feature_id=feature.id,
            prerequisite_feature_id=prerequisite.id,
        ),
    )

    # Then
    assert response.status_code == 404
    assert response.json() == {"code": "feature_not_found", "message": message}
    assert not Segment.objects.filter(feature=feature).exists()
    assert not SegmentFlagReference.objects.exists()
    assert list(AuditLog.objects.filter(related_object_type="FEATURE")) == []
    assert not log.has("dependencies.created")


def test_add_feature_dependency__missing_environment_permission__responds_403_with_error(
    environment: int,
    environment_api_key: str,
    log: StructuredLogCapture,
    organisation: int,
    project: int,
    staff_client: APIClient,
    staff_user: FFAdminUser,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
) -> None:
    # Given
    feature = Feature.objects.create(name="checkout", project_id=project)
    prerequisite = Feature.objects.create(name="payments", project_id=project)
    staff_user.add_organisation(Organisation.objects.get(id=organisation))
    with_environment_permissions([UPDATE_FEATURE_STATE], environment, False)

    # When
    response = staff_client.post(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/{prerequisite.id}/",
    )

    # Then
    assert response.status_code == 403
    assert response.json() == {
        "code": "permission_denied",
        "message": 'The permission "Manage segment overrides" is necessary to manage feature dependencies.',
    }
    assert not Segment.objects.filter(feature=feature).exists()
    assert not SegmentFlagReference.objects.exists()
    assert list(AuditLog.objects.filter(related_object_type="FEATURE")) == []
    assert not log.has("dependencies.created")
