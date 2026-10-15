from datetime import timedelta

import pytest
from common.environments.permissions import MANAGE_SEGMENT_OVERRIDES
from django.conf import settings
from django.utils import timezone
from freezegun.api import FrozenDateTimeFactory
from pytest_structlog import StructuredLogCapture
from rest_framework.test import APIClient

from environments.models import Environment
from features.dependencies.exceptions import PrerequisiteHasPrerequisiteError
from features.dependencies.types import DependencyEdge
from features.models import Feature
from features.versioning.tasks import publish_version_change_set
from features.workflows.core.models import ChangeRequest, ChangeRequestApproval
from organisations.models import Organisation
from segments.models import Segment
from tests.integration.types import (
    AddFeaturePrerequisiteFixture,
    CreateChangeRequestFixture,
    GetFeatureFixture,
)
from tests.types import CaptureAuditLogsFixture, WithEnvironmentPermissionsCallable
from users.models import FFAdminUser

pytestmark = [
    pytest.mark.skipif(
        not settings.WORKFLOWS_LOGIC_INSTALLED,
        reason="workflows_logic module not installed (private package extra)",
    ),
    pytest.mark.usefixtures("environment_v2_versioning"),
]


def _enable_change_requests(environment: int) -> None:
    Environment.objects.filter(id=environment).update(
        minimum_change_request_approvals=1,
    )


def _approve_change_request(
    change_request: ChangeRequest, approver: FFAdminUser
) -> None:
    ChangeRequestApproval.objects.create(
        change_request=change_request,
        user=approver,
        approved_at=timezone.now(),
    )


# Direct dependency changes but change requests are enabled


def test_add_feature_dependency__bare_but_change_requests_enabled__responds_409(
    admin_client: APIClient,
    capture_audit_logs: CaptureAuditLogsFixture,
    environment: int,
    environment_api_key: str,
    get_feature: GetFeatureFixture,
    log: StructuredLogCapture,
    project: int,
) -> None:
    # Given
    feature = Feature.objects.create(name="checkout", project_id=project)
    prerequisite = Feature.objects.create(name="payments", project_id=project)
    _enable_change_requests(environment)

    # When
    with capture_audit_logs() as audit_logs:
        response = admin_client.post(
            f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/{prerequisite.id}/",
        )

    # Then
    assert response.status_code == 409
    assert response.json() == {
        "code": "change_requests_enabled",
        "message": "Cannot make this change where change requests are enabled.",
    }
    assert not Segment.objects.filter(feature=feature).exists()
    assert get_feature(environment_api_key, feature.id)["segment_overrides"] == []
    assert list(audit_logs) == []
    assert not log.has("dependencies.created")


def test_delete_feature_dependency__bare_but_change_requests_enabled__responds_409(
    add_feature_prerequisite: AddFeaturePrerequisiteFixture,
    admin_client: APIClient,
    capture_audit_logs: CaptureAuditLogsFixture,
    environment: int,
    environment_api_key: str,
    get_feature: GetFeatureFixture,
    log: StructuredLogCapture,
    project: int,
) -> None:
    # Given
    feature = Feature.objects.create(name="checkout", project_id=project)
    prerequisite = Feature.objects.create(name="payments", project_id=project)
    add_feature_prerequisite(environment_api_key, feature.id, prerequisite.id)
    _enable_change_requests(environment)

    # When
    with capture_audit_logs() as audit_logs:
        response = admin_client.delete(
            f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/{prerequisite.id}/",
        )

    # Then
    assert response.status_code == 409
    assert response.json() == {
        "code": "change_requests_enabled",
        "message": "Cannot make this change where change requests are enabled.",
    }
    assert len(get_feature(environment_api_key, feature.id)["segment_overrides"]) == 1
    assert list(audit_logs) == []
    assert not log.has("dependencies.deleted")


# Open change requests


def test_add_feature_dependency__point_to_open_change_request__responds_201(
    admin_client: APIClient,
    capture_audit_logs: CaptureAuditLogsFixture,
    create_change_request: CreateChangeRequestFixture,
    environment: int,
    environment_api_key: str,
    log: StructuredLogCapture,
    project: int,
) -> None:
    # Given
    feature = Feature.objects.create(name="checkout", project_id=project)
    prerequisite = Feature.objects.create(name="payments", project_id=project)
    _enable_change_requests(environment)
    change_request = create_change_request(feature.id, title="Pending")

    # When
    with capture_audit_logs() as audit_logs:
        response = admin_client.post(
            f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/{prerequisite.id}/?change_request={change_request.id}",
        )

    # Then
    assert response.status_code == 201
    assert response.json() == (
        dependency := DependencyEdge(
            {
                "feature": {"id": feature.id, "name": "checkout"},
                "prerequisite": {"id": prerequisite.id, "name": "payments"},
                "segment": {
                    "id": response.json()["segment"]["id"],
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
    )
    assert admin_client.get(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/?change_request={change_request.id}",
    ).json() == {"results": [dependency]}
    assert admin_client.get(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/",
    ).json() == {"results": []}
    assert list(audit_logs) == []
    assert not log.has("dependencies.created")


def test_delete_feature_dependency__point_to_open_change_request__responds_204(
    add_feature_prerequisite: AddFeaturePrerequisiteFixture,
    admin_client: APIClient,
    capture_audit_logs: CaptureAuditLogsFixture,
    create_change_request: CreateChangeRequestFixture,
    environment: int,
    environment_api_key: str,
    log: StructuredLogCapture,
    project: int,
) -> None:
    # Given
    feature = Feature.objects.create(name="checkout", project_id=project)
    prerequisite = Feature.objects.create(name="payments", project_id=project)
    live_dependency = add_feature_prerequisite(
        environment_api_key, feature.id, prerequisite.id
    )
    _enable_change_requests(environment)
    change_request = create_change_request(feature.id, title="Pending")

    # When
    with capture_audit_logs() as audit_logs:
        response = admin_client.delete(
            f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/{prerequisite.id}/?change_request={change_request.id}",
        )

    # Then
    assert response.status_code == 204
    assert admin_client.get(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/?change_request={change_request.id}",
    ).json() == {"results": []}
    assert admin_client.get(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/",
    ).json() == {"results": [live_dependency]}
    assert list(audit_logs) == []
    assert not log.has("dependencies.deleted")


def test_list_feature_dependencies__point_to_open_change_request__responds_200(
    add_feature_prerequisite: AddFeaturePrerequisiteFixture,
    admin_client: APIClient,
    capture_audit_logs: CaptureAuditLogsFixture,
    create_change_request: CreateChangeRequestFixture,
    environment: int,
    environment_api_key: str,
    project: int,
) -> None:
    # Given
    feature = Feature.objects.create(name="checkout", project_id=project)
    payments = Feature.objects.create(name="payments", project_id=project)
    inventory = Feature.objects.create(name="inventory", project_id=project)
    shipping = Feature.objects.create(name="shipping", project_id=project)
    live_payments_dependency = add_feature_prerequisite(
        environment_api_key, feature.id, payments.id
    )
    live_inventory_dependency = add_feature_prerequisite(
        environment_api_key, feature.id, inventory.id
    )
    _enable_change_requests(environment)
    change_request = create_change_request(feature.id, title="Pending")
    staged_shipping_dependency = admin_client.post(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/{shipping.id}/?change_request={change_request.id}",
    ).json()
    admin_client.delete(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/{inventory.id}/?change_request={change_request.id}",
    )

    # When
    with capture_audit_logs() as audit_logs:
        response = admin_client.get(
            f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/?change_request={change_request.id}",
        )

    # Then
    assert response.status_code == 200
    assert response.json() == {
        "results": [live_payments_dependency, staged_shipping_dependency]
    }
    assert admin_client.get(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/",
    ).json() == {"results": [live_payments_dependency, live_inventory_dependency]}
    assert list(audit_logs) == []


# Approved change requests


def test_add_feature_dependency__point_to_approved_change_request__responds_400(
    admin_client: APIClient,
    admin_user: FFAdminUser,
    capture_audit_logs: CaptureAuditLogsFixture,
    create_change_request: CreateChangeRequestFixture,
    environment: int,
    environment_api_key: str,
    log: StructuredLogCapture,
    project: int,
) -> None:
    # Given
    feature = Feature.objects.create(name="checkout", project_id=project)
    prerequisite = Feature.objects.create(name="payments", project_id=project)
    _enable_change_requests(environment)
    change_request = create_change_request(feature.id, title="Approved")
    _approve_change_request(change_request, admin_user)

    # When
    with capture_audit_logs() as audit_logs:
        response = admin_client.post(
            f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/{prerequisite.id}/?change_request={change_request.id}",
        )

    # Then
    assert response.status_code == 400
    assert response.json() == {
        "code": "change_request_approved",
        "message": "Cannot change an approved change request.",
    }
    assert admin_client.get(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/?change_request={change_request.id}",
    ).json() == {"results": []}
    assert admin_client.get(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/",
    ).json() == {"results": []}
    assert list(audit_logs) == []
    assert not log.has("dependencies.created")


def test_delete_feature_dependency__point_to_approved_change_request__responds_400(
    add_feature_prerequisite: AddFeaturePrerequisiteFixture,
    admin_client: APIClient,
    admin_user: FFAdminUser,
    capture_audit_logs: CaptureAuditLogsFixture,
    create_change_request: CreateChangeRequestFixture,
    environment: int,
    environment_api_key: str,
    log: StructuredLogCapture,
    project: int,
) -> None:
    # Given
    feature = Feature.objects.create(name="checkout", project_id=project)
    prerequisite = Feature.objects.create(name="payments", project_id=project)
    live_dependency = add_feature_prerequisite(
        environment_api_key, feature.id, prerequisite.id
    )
    _enable_change_requests(environment)
    change_request = create_change_request(feature.id, title="Approved")
    _approve_change_request(change_request, admin_user)

    # When
    with capture_audit_logs() as audit_logs:
        response = admin_client.delete(
            f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/{prerequisite.id}/?change_request={change_request.id}",
        )

    # Then
    assert response.status_code == 400
    assert response.json() == {
        "code": "change_request_approved",
        "message": "Cannot change an approved change request.",
    }
    assert admin_client.get(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/?change_request={change_request.id}",
    ).json() == {"results": [live_dependency]}
    assert admin_client.get(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/",
    ).json() == {"results": [live_dependency]}
    assert list(audit_logs) == []
    assert not log.has("dependencies.deleted")


def test_list_feature_dependencies__point_to_approved_change_request__responds_200(
    add_feature_prerequisite: AddFeaturePrerequisiteFixture,
    admin_client: APIClient,
    admin_user: FFAdminUser,
    capture_audit_logs: CaptureAuditLogsFixture,
    create_change_request: CreateChangeRequestFixture,
    environment: int,
    environment_api_key: str,
    project: int,
) -> None:
    # Given
    feature = Feature.objects.create(name="checkout", project_id=project)
    payments = Feature.objects.create(name="payments", project_id=project)
    inventory = Feature.objects.create(name="inventory", project_id=project)
    shipping = Feature.objects.create(name="shipping", project_id=project)
    live_payments_dependency = add_feature_prerequisite(
        environment_api_key, feature.id, payments.id
    )
    live_inventory_dependency = add_feature_prerequisite(
        environment_api_key, feature.id, inventory.id
    )
    _enable_change_requests(environment)
    change_request = create_change_request(feature.id, title="Approved")
    staged_shipping_dependency = admin_client.post(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/{shipping.id}/?change_request={change_request.id}",
    ).json()
    admin_client.delete(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/{inventory.id}/?change_request={change_request.id}",
    )
    _approve_change_request(change_request, admin_user)

    # When
    with capture_audit_logs() as audit_logs:
        response = admin_client.get(
            f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/?change_request={change_request.id}",
        )

    # Then
    assert response.status_code == 200
    assert response.json() == {
        "results": [live_payments_dependency, staged_shipping_dependency]
    }
    assert admin_client.get(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/",
    ).json() == {"results": [live_payments_dependency, live_inventory_dependency]}
    assert list(audit_logs) == []


# Committed change requests


def test_add_feature_dependency__point_to_committed_change_request__responds_400(
    admin_client: APIClient,
    admin_user: FFAdminUser,
    capture_audit_logs: CaptureAuditLogsFixture,
    create_change_request: CreateChangeRequestFixture,
    environment: int,
    environment_api_key: str,
    log: StructuredLogCapture,
    project: int,
) -> None:
    # Given
    feature = Feature.objects.create(name="checkout", project_id=project)
    prerequisite = Feature.objects.create(name="payments", project_id=project)
    _enable_change_requests(environment)
    change_request = create_change_request(feature.id, title="Committed")
    _approve_change_request(change_request, admin_user)
    change_request.commit(committed_by=admin_user)

    # When
    with capture_audit_logs() as audit_logs:
        response = admin_client.post(
            f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/{prerequisite.id}/?change_request={change_request.id}",
        )

    # Then
    assert response.status_code == 400
    assert response.json() == {
        "code": "change_request_committed",
        "message": "The change request is already committed.",
    }
    assert admin_client.get(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/",
    ).json() == {"results": []}
    assert list(audit_logs) == []
    assert not log.has("dependencies.created")


def test_delete_feature_dependency__point_to_committed_change_request__responds_400(
    add_feature_prerequisite: AddFeaturePrerequisiteFixture,
    admin_client: APIClient,
    admin_user: FFAdminUser,
    capture_audit_logs: CaptureAuditLogsFixture,
    create_change_request: CreateChangeRequestFixture,
    environment: int,
    environment_api_key: str,
    log: StructuredLogCapture,
    project: int,
) -> None:
    # Given
    feature = Feature.objects.create(name="checkout", project_id=project)
    prerequisite = Feature.objects.create(name="payments", project_id=project)
    live_dependency = add_feature_prerequisite(
        environment_api_key, feature.id, prerequisite.id
    )
    _enable_change_requests(environment)
    change_request = create_change_request(feature.id, title="Committed")
    _approve_change_request(change_request, admin_user)
    change_request.commit(committed_by=admin_user)

    # When
    with capture_audit_logs() as audit_logs:
        response = admin_client.delete(
            f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/{prerequisite.id}/?change_request={change_request.id}",
        )

    # Then
    assert response.status_code == 400
    assert response.json() == {
        "code": "change_request_committed",
        "message": "The change request is already committed.",
    }
    assert admin_client.get(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/",
    ).json() == {"results": [live_dependency]}
    assert list(audit_logs) == []
    assert not log.has("dependencies.deleted")


def test_list_feature_dependencies__point_to_committed_change_request__responds_400(
    add_feature_prerequisite: AddFeaturePrerequisiteFixture,
    admin_client: APIClient,
    admin_user: FFAdminUser,
    capture_audit_logs: CaptureAuditLogsFixture,
    create_change_request: CreateChangeRequestFixture,
    environment: int,
    environment_api_key: str,
    project: int,
) -> None:
    # Given
    feature = Feature.objects.create(name="checkout", project_id=project)
    payments = Feature.objects.create(name="payments", project_id=project)
    inventory = Feature.objects.create(name="inventory", project_id=project)
    shipping = Feature.objects.create(name="shipping", project_id=project)
    live_payments_dependency = add_feature_prerequisite(
        environment_api_key, feature.id, payments.id
    )
    add_feature_prerequisite(environment_api_key, feature.id, inventory.id)
    _enable_change_requests(environment)
    change_request = create_change_request(feature.id, title="Committed")
    staged_shipping_dependency = admin_client.post(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/{shipping.id}/?change_request={change_request.id}",
    ).json()
    admin_client.delete(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/{inventory.id}/?change_request={change_request.id}",
    )
    _approve_change_request(change_request, admin_user)
    change_request.commit(committed_by=admin_user)

    # When
    with capture_audit_logs() as audit_logs:
        response = admin_client.get(
            f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/?change_request={change_request.id}",
        )

    # Then
    assert response.status_code == 400
    assert response.json() == {
        "code": "change_request_committed",
        "message": "The change request is already committed.",
    }
    assert admin_client.get(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/",
    ).json() == {"results": [live_payments_dependency, staged_shipping_dependency]}
    assert list(audit_logs) == []


# Unusable change requests


def test_list_feature_dependencies__point_to_unknown_change_request__responds_404(
    admin_client: APIClient,
    environment: int,
    environment_api_key: str,
    project: int,
) -> None:
    # Given
    feature = Feature.objects.create(name="checkout", project_id=project)
    _enable_change_requests(environment)

    # When
    response = admin_client.get(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/?change_request=999999",
    )

    # Then
    assert response.status_code == 404
    assert response.json() == {
        "code": "change_request_not_found",
        "message": "Change request not found.",
    }


def test_add_feature_dependency__change_requests_disabled__responds_409(
    admin_client: APIClient,
    admin_user: FFAdminUser,
    capture_audit_logs: CaptureAuditLogsFixture,
    environment: int,
    environment_api_key: str,
    log: StructuredLogCapture,
    project: int,
) -> None:
    # Given
    feature = Feature.objects.create(name="checkout", project_id=project)
    prerequisite = Feature.objects.create(name="payments", project_id=project)
    change_request = ChangeRequest.objects.create(
        environment_id=environment, title="Pending", user=admin_user
    )

    # When
    with capture_audit_logs() as audit_logs:
        response = admin_client.post(
            f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/{prerequisite.id}/?change_request={change_request.id}",
        )

    # Then
    assert response.status_code == 409
    assert response.json() == {
        "code": "change_requests_disabled",
        "message": "Enable Feature Change Requests to change dependencies in change requests.",
    }
    assert admin_client.get(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/",
    ).json() == {"results": []}
    assert list(audit_logs) == []
    assert not log.has("dependencies.created")


# Feature versioning v1


@pytest.mark.parametrize("environment_v2_versioning", [None])
def test_add_feature_dependency__feature_versioning_v1__responds_409(
    admin_client: APIClient,
    admin_user: FFAdminUser,
    capture_audit_logs: CaptureAuditLogsFixture,
    environment: int,
    environment_api_key: str,
    log: StructuredLogCapture,
    project: int,
) -> None:
    # Given
    feature = Feature.objects.create(name="checkout", project_id=project)
    prerequisite = Feature.objects.create(name="payments", project_id=project)
    _enable_change_requests(environment)
    change_request = ChangeRequest.objects.create(
        environment_id=environment, title="Pending", user=admin_user
    )

    # When
    with capture_audit_logs() as audit_logs:
        response = admin_client.post(
            f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/{prerequisite.id}/?change_request={change_request.id}",
        )

    # Then
    assert response.status_code == 409
    assert response.json() == {
        "code": "feature_versioning_disabled",
        "message": "Enable Feature Versioning to change dependencies in change requests.",
    }
    assert not Segment.objects.filter(feature=feature).exists()
    assert admin_client.get(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/",
    ).json() == {"results": []}
    assert list(audit_logs) == []
    assert not log.has("dependencies.created")


@pytest.mark.parametrize("environment_v2_versioning", [None])
def test_delete_feature_dependency__feature_versioning_v1__responds_409(
    add_feature_prerequisite: AddFeaturePrerequisiteFixture,
    admin_client: APIClient,
    admin_user: FFAdminUser,
    capture_audit_logs: CaptureAuditLogsFixture,
    environment: int,
    environment_api_key: str,
    log: StructuredLogCapture,
    project: int,
) -> None:
    # Given
    feature = Feature.objects.create(name="checkout", project_id=project)
    prerequisite = Feature.objects.create(name="payments", project_id=project)
    live_dependency = add_feature_prerequisite(
        environment_api_key, feature.id, prerequisite.id
    )
    _enable_change_requests(environment)
    change_request = ChangeRequest.objects.create(
        environment_id=environment, title="Pending", user=admin_user
    )

    # When
    with capture_audit_logs() as audit_logs:
        response = admin_client.delete(
            f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/{prerequisite.id}/?change_request={change_request.id}",
        )

    # Then
    assert response.status_code == 409
    assert response.json() == {
        "code": "feature_versioning_disabled",
        "message": "Enable Feature Versioning to change dependencies in change requests.",
    }
    assert admin_client.get(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/",
    ).json() == {"results": [live_dependency]}
    assert list(audit_logs) == []
    assert not log.has("dependencies.deleted")


# Lacking permission


def test_add_feature_dependency__lacking_permission__responds_403(
    admin_client: APIClient,
    capture_audit_logs: CaptureAuditLogsFixture,
    create_change_request: CreateChangeRequestFixture,
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
    _enable_change_requests(environment)
    change_request = create_change_request(feature.id, title="Pending")
    staff_user.add_organisation(Organisation.objects.get(id=organisation))
    with_environment_permissions([MANAGE_SEGMENT_OVERRIDES], environment, False)

    # When
    with capture_audit_logs() as audit_logs:
        response = staff_client.post(
            f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/{prerequisite.id}/?change_request={change_request.id}",
        )

    # Then
    assert response.status_code == 403
    assert response.json() == {
        "code": "permission_denied",
        "message": 'The permission "Create change request" is necessary to change dependencies in change requests.',
    }
    assert admin_client.get(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/?change_request={change_request.id}",
    ).json() == {"results": []}
    assert list(audit_logs) == []
    assert not log.has("dependencies.created")


def test_delete_feature_dependency__lacking_permission__responds_403(
    add_feature_prerequisite: AddFeaturePrerequisiteFixture,
    admin_client: APIClient,
    capture_audit_logs: CaptureAuditLogsFixture,
    create_change_request: CreateChangeRequestFixture,
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
    live_dependency = add_feature_prerequisite(
        environment_api_key, feature.id, prerequisite.id
    )
    _enable_change_requests(environment)
    change_request = create_change_request(feature.id, title="Pending")
    staff_user.add_organisation(Organisation.objects.get(id=organisation))
    with_environment_permissions([MANAGE_SEGMENT_OVERRIDES], environment, False)

    # When
    with capture_audit_logs() as audit_logs:
        response = staff_client.delete(
            f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/{prerequisite.id}/?change_request={change_request.id}",
        )

    # Then
    assert response.status_code == 403
    assert response.json() == {
        "code": "permission_denied",
        "message": 'The permission "Create change request" is necessary to change dependencies in change requests.',
    }
    assert admin_client.get(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/?change_request={change_request.id}",
    ).json() == {"results": [live_dependency]}
    assert list(audit_logs) == []
    assert not log.has("dependencies.deleted")


def test_add_feature_dependency__unrelated_to_environment__responds_404(
    admin_client: APIClient,
    capture_audit_logs: CaptureAuditLogsFixture,
    create_change_request: CreateChangeRequestFixture,
    environment: int,
    environment_api_key: str,
    log: StructuredLogCapture,
    project: int,
    staff_client: APIClient,
) -> None:
    # Given
    feature = Feature.objects.create(name="checkout", project_id=project)
    prerequisite = Feature.objects.create(name="payments", project_id=project)
    _enable_change_requests(environment)
    change_request = create_change_request(feature.id, title="Pending")

    # When
    with capture_audit_logs() as audit_logs:
        response = staff_client.post(
            f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/{prerequisite.id}/?change_request={change_request.id}",
        )

    # Then
    assert response.status_code == 404
    assert response.json() == {
        "code": "environment_not_found",
        "message": f"Environment key '{environment_api_key}' does not exist.",
    }
    assert admin_client.get(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/?change_request={change_request.id}",
    ).json() == {"results": []}
    assert list(audit_logs) == []
    assert not log.has("dependencies.created")


# Stage hygiene


def test_delete_feature_dependency__previously_staged__responds_204_undoing_staged(
    admin_client: APIClient,
    capture_audit_logs: CaptureAuditLogsFixture,
    create_change_request: CreateChangeRequestFixture,
    environment: int,
    environment_api_key: str,
    log: StructuredLogCapture,
    project: int,
) -> None:
    # Given
    feature = Feature.objects.create(name="checkout", project_id=project)
    prerequisite = Feature.objects.create(name="payments", project_id=project)
    _enable_change_requests(environment)
    change_request = create_change_request(feature.id, title="Pending")
    admin_client.post(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/{prerequisite.id}/?change_request={change_request.id}",
    )

    # When
    with capture_audit_logs() as audit_logs:
        response = admin_client.delete(
            f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/{prerequisite.id}/?change_request={change_request.id}",
        )

    # Then
    assert response.status_code == 204
    assert admin_client.get(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/?change_request={change_request.id}",
    ).json() == {"results": []}
    assert admin_client.get(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/",
    ).json() == {"results": []}
    assert list(audit_logs) == []
    assert not log.has("dependencies.created")
    assert not log.has("dependencies.deleted")


def test_add_feature_dependency__previously_staged_for_deletion__responds_201_keeping_live(
    add_feature_prerequisite: AddFeaturePrerequisiteFixture,
    admin_client: APIClient,
    capture_audit_logs: CaptureAuditLogsFixture,
    create_change_request: CreateChangeRequestFixture,
    environment: int,
    environment_api_key: str,
    log: StructuredLogCapture,
    project: int,
) -> None:
    # Given
    feature = Feature.objects.create(name="checkout", project_id=project)
    prerequisite = Feature.objects.create(name="payments", project_id=project)
    live_dependency = add_feature_prerequisite(
        environment_api_key, feature.id, prerequisite.id
    )
    _enable_change_requests(environment)
    change_request = create_change_request(feature.id, title="Pending")
    admin_client.delete(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/{prerequisite.id}/?change_request={change_request.id}",
    )

    # When
    with capture_audit_logs() as audit_logs:
        response = admin_client.post(
            f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/{prerequisite.id}/?change_request={change_request.id}",
        )

    # Then
    assert response.status_code == 201
    assert response.json() == live_dependency
    assert admin_client.get(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/?change_request={change_request.id}",
    ).json() == {"results": [live_dependency]}
    assert admin_client.get(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/",
    ).json() == {"results": [live_dependency]}
    assert list(audit_logs) == []
    assert not log.has("dependencies.deleted")


def test_add_feature_dependency__previously_staged__responds_400_leaving_one_staged(
    admin_client: APIClient,
    capture_audit_logs: CaptureAuditLogsFixture,
    create_change_request: CreateChangeRequestFixture,
    environment: int,
    environment_api_key: str,
    environment_name: str,
    log: StructuredLogCapture,
    project: int,
) -> None:
    # Given
    feature = Feature.objects.create(name="checkout", project_id=project)
    prerequisite = Feature.objects.create(name="payments", project_id=project)
    _enable_change_requests(environment)
    change_request = create_change_request(feature.id, title="Pending")
    staged_dependency = admin_client.post(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/{prerequisite.id}/?change_request={change_request.id}",
    ).json()

    # When
    with capture_audit_logs() as audit_logs:
        response = admin_client.post(
            f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/{prerequisite.id}/?change_request={change_request.id}",
        )

    # Then
    assert response.status_code == 400
    assert response.json() == {
        "code": "dependency_exists",
        "message": 'The feature "checkout" already depends on the feature "payments".',
        "environment": {"key": environment_api_key, "name": environment_name},
        "path": [staged_dependency],
    }
    assert admin_client.get(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/?change_request={change_request.id}",
    ).json() == {"results": [staged_dependency]}
    assert admin_client.get(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/",
    ).json() == {"results": []}
    assert list(audit_logs) == []
    assert not log.has("dependencies.created")


# Prerequisite depth


def test_add_feature_dependency__prerequisite_has_live_prerequisite__responds_400(
    add_feature_prerequisite: AddFeaturePrerequisiteFixture,
    admin_client: APIClient,
    capture_audit_logs: CaptureAuditLogsFixture,
    create_change_request: CreateChangeRequestFixture,
    environment: int,
    environment_api_key: str,
    environment_name: str,
    log: StructuredLogCapture,
    project: int,
) -> None:
    # Given
    checkout = Feature.objects.create(name="checkout", project_id=project)
    payments = Feature.objects.create(name="payments", project_id=project)
    inventory = Feature.objects.create(name="inventory", project_id=project)
    live_inventory_dependency = add_feature_prerequisite(
        environment_api_key, payments.id, inventory.id
    )
    _enable_change_requests(environment)
    change_request = create_change_request(checkout.id, title="Pending")

    # When
    with capture_audit_logs() as audit_logs:
        response = admin_client.post(
            f"/api/v1/environments/{environment_api_key}/features/{checkout.id}/dependencies/{payments.id}/?change_request={change_request.id}",
        )

    # Then
    assert response.status_code == 400
    assert response.json() == {
        "code": "prerequisite_has_prerequisite",
        "message": 'The prerequisite "payments" already has a prerequisite "inventory".',
        "environment": {"key": environment_api_key, "name": environment_name},
        "path": [live_inventory_dependency],
    }
    assert admin_client.get(
        f"/api/v1/environments/{environment_api_key}/features/{checkout.id}/dependencies/?change_request={change_request.id}",
    ).json() == {"results": []}
    assert list(audit_logs) == []
    assert not log.has("dependencies.created", feature__name="checkout")


def test_add_feature_dependency__prerequisite_has_scheduled_prerequisite__responds_400(
    admin_client: APIClient,
    admin_user: FFAdminUser,
    capture_audit_logs: CaptureAuditLogsFixture,
    create_change_request: CreateChangeRequestFixture,
    environment: int,
    environment_api_key: str,
    environment_name: str,
    log: StructuredLogCapture,
    project: int,
) -> None:
    # Given
    checkout = Feature.objects.create(name="checkout", project_id=project)
    payments = Feature.objects.create(name="payments", project_id=project)
    inventory = Feature.objects.create(name="inventory", project_id=project)
    _enable_change_requests(environment)
    scheduled_change_request = create_change_request(
        payments.id, title="Scheduled", live_from=timezone.now() + timedelta(days=1)
    )
    scheduled_inventory_dependency = admin_client.post(
        f"/api/v1/environments/{environment_api_key}/features/{payments.id}/dependencies/{inventory.id}/?change_request={scheduled_change_request.id}",
    ).json()
    _approve_change_request(scheduled_change_request, admin_user)
    scheduled_change_request.commit(committed_by=admin_user)
    change_request = create_change_request(checkout.id, title="Pending")

    # When
    with capture_audit_logs() as audit_logs:
        response = admin_client.post(
            f"/api/v1/environments/{environment_api_key}/features/{checkout.id}/dependencies/{payments.id}/?change_request={change_request.id}",
        )

    # Then
    assert response.status_code == 400
    assert response.json() == {
        "code": "prerequisite_has_prerequisite",
        "message": 'The prerequisite "payments" already has a prerequisite "inventory".',
        "environment": {"key": environment_api_key, "name": environment_name},
        "path": [scheduled_inventory_dependency],
    }
    assert admin_client.get(
        f"/api/v1/environments/{environment_api_key}/features/{checkout.id}/dependencies/?change_request={change_request.id}",
    ).json() == {"results": []}
    assert list(audit_logs) == []
    assert not log.has("dependencies.created")


def test_add_feature_dependency__prerequisite_has_prerequisite_scheduled_for_deletion__responds_400(
    add_feature_prerequisite: AddFeaturePrerequisiteFixture,
    admin_client: APIClient,
    admin_user: FFAdminUser,
    capture_audit_logs: CaptureAuditLogsFixture,
    create_change_request: CreateChangeRequestFixture,
    environment: int,
    environment_api_key: str,
    environment_name: str,
    log: StructuredLogCapture,
    project: int,
) -> None:
    # Given
    checkout = Feature.objects.create(name="checkout", project_id=project)
    payments = Feature.objects.create(name="payments", project_id=project)
    inventory = Feature.objects.create(name="inventory", project_id=project)
    live_inventory_dependency = add_feature_prerequisite(
        environment_api_key, payments.id, inventory.id
    )
    _enable_change_requests(environment)
    scheduled_change_request = create_change_request(
        payments.id, title="Scheduled", live_from=timezone.now() + timedelta(days=1)
    )
    admin_client.delete(
        f"/api/v1/environments/{environment_api_key}/features/{payments.id}/dependencies/{inventory.id}/?change_request={scheduled_change_request.id}",
    )
    _approve_change_request(scheduled_change_request, admin_user)
    scheduled_change_request.commit(committed_by=admin_user)
    change_request = create_change_request(checkout.id, title="Pending")

    # When
    with capture_audit_logs() as audit_logs:
        response = admin_client.post(
            f"/api/v1/environments/{environment_api_key}/features/{checkout.id}/dependencies/{payments.id}/?change_request={change_request.id}",
        )

    # Then
    assert response.status_code == 400
    assert response.json() == {
        "code": "prerequisite_has_prerequisite",
        "message": 'The prerequisite "payments" already has a prerequisite "inventory".',
        "environment": {"key": environment_api_key, "name": environment_name},
        "path": [live_inventory_dependency],
    }
    assert admin_client.get(
        f"/api/v1/environments/{environment_api_key}/features/{checkout.id}/dependencies/?change_request={change_request.id}",
    ).json() == {"results": []}
    assert list(audit_logs) == []
    assert not log.has("dependencies.created", feature__name="checkout")


def test_add_feature_dependency__feature_is_prerequisite_scheduled_for_deletion__responds_400(
    add_feature_prerequisite: AddFeaturePrerequisiteFixture,
    admin_client: APIClient,
    admin_user: FFAdminUser,
    capture_audit_logs: CaptureAuditLogsFixture,
    create_change_request: CreateChangeRequestFixture,
    environment: int,
    environment_api_key: str,
    environment_name: str,
    log: StructuredLogCapture,
    project: int,
) -> None:
    # Given
    checkout = Feature.objects.create(name="checkout", project_id=project)
    payments = Feature.objects.create(name="payments", project_id=project)
    inventory = Feature.objects.create(name="inventory", project_id=project)
    live_payments_dependency = add_feature_prerequisite(
        environment_api_key, checkout.id, payments.id
    )
    _enable_change_requests(environment)
    scheduled_change_request = create_change_request(
        checkout.id, title="Scheduled", live_from=timezone.now() + timedelta(days=1)
    )
    admin_client.delete(
        f"/api/v1/environments/{environment_api_key}/features/{checkout.id}/dependencies/{payments.id}/?change_request={scheduled_change_request.id}",
    )
    _approve_change_request(scheduled_change_request, admin_user)
    scheduled_change_request.commit(committed_by=admin_user)
    change_request = create_change_request(payments.id, title="Pending")

    # When
    with capture_audit_logs() as audit_logs:
        response = admin_client.post(
            f"/api/v1/environments/{environment_api_key}/features/{payments.id}/dependencies/{inventory.id}/?change_request={change_request.id}",
        )

    # Then
    assert response.status_code == 400
    assert response.json() == {
        "code": "feature_is_prerequisite",
        "message": 'The feature "payments" is already a prerequisite for the feature "checkout".',
        "environment": {"key": environment_api_key, "name": environment_name},
        "path": [live_payments_dependency],
    }
    assert admin_client.get(
        f"/api/v1/environments/{environment_api_key}/features/{payments.id}/dependencies/?change_request={change_request.id}",
    ).json() == {"results": []}
    assert list(audit_logs) == []
    assert not log.has("dependencies.created", feature__name="payments")


def test_commit_change_request__prerequisite_gained_prerequisite_since_staged__raises_and_publishes_nothing(
    admin_client: APIClient,
    admin_user: FFAdminUser,
    capture_audit_logs: CaptureAuditLogsFixture,
    create_change_request: CreateChangeRequestFixture,
    environment: int,
    environment_api_key: str,
    log: StructuredLogCapture,
    organisation: int,
    project: int,
) -> None:
    # Given
    checkout = Feature.objects.create(name="checkout", project_id=project)
    payments = Feature.objects.create(name="payments", project_id=project)
    inventory = Feature.objects.create(name="inventory", project_id=project)
    _enable_change_requests(environment)
    payments_change_request = create_change_request(payments.id, title="Payments")
    admin_client.post(
        f"/api/v1/environments/{environment_api_key}/features/{payments.id}/dependencies/{inventory.id}/?change_request={payments_change_request.id}",
    )
    checkout_change_request = create_change_request(checkout.id, title="Checkout")
    admin_client.post(
        f"/api/v1/environments/{environment_api_key}/features/{checkout.id}/dependencies/{payments.id}/?change_request={checkout_change_request.id}",
    )
    _approve_change_request(payments_change_request, admin_user)
    _approve_change_request(checkout_change_request, admin_user)
    payments_change_request.commit(committed_by=admin_user)

    # When
    with capture_audit_logs() as audit_logs:
        with pytest.raises(PrerequisiteHasPrerequisiteError):
            checkout_change_request.commit(committed_by=admin_user)

    # Then
    checkout_change_request.refresh_from_db()
    assert checkout_change_request.committed_at is None
    assert admin_client.get(
        f"/api/v1/environments/{environment_api_key}/features/{checkout.id}/dependencies/",
    ).json() == {"results": []}
    assert list(audit_logs) == []
    assert log.has(
        "dependencies.create_failed",
        level="info",
        organisation__id=organisation,
        project__id=project,
        environment__key=environment_api_key,
        feature__name="checkout",
        prerequisite_feature__name="payments",
    )


def test_commit_change_request__prerequisite_has_prerequisite_scheduled_for_deletion__raises_and_publishes_nothing(
    admin_client: APIClient,
    admin_user: FFAdminUser,
    capture_audit_logs: CaptureAuditLogsFixture,
    create_change_request: CreateChangeRequestFixture,
    environment: int,
    environment_api_key: str,
    log: StructuredLogCapture,
    organisation: int,
    project: int,
) -> None:
    # Given
    checkout = Feature.objects.create(name="checkout", project_id=project)
    payments = Feature.objects.create(name="payments", project_id=project)
    inventory = Feature.objects.create(name="inventory", project_id=project)
    _enable_change_requests(environment)
    checkout_change_request = create_change_request(checkout.id, title="Checkout")
    admin_client.post(
        f"/api/v1/environments/{environment_api_key}/features/{checkout.id}/dependencies/{payments.id}/?change_request={checkout_change_request.id}",
    )
    payments_change_request = create_change_request(payments.id, title="Payments")
    admin_client.post(
        f"/api/v1/environments/{environment_api_key}/features/{payments.id}/dependencies/{inventory.id}/?change_request={payments_change_request.id}",
    )
    _approve_change_request(payments_change_request, admin_user)
    payments_change_request.commit(committed_by=admin_user)
    scheduled_change_request = create_change_request(
        payments.id, title="Scheduled", live_from=timezone.now() + timedelta(days=1)
    )
    admin_client.delete(
        f"/api/v1/environments/{environment_api_key}/features/{payments.id}/dependencies/{inventory.id}/?change_request={scheduled_change_request.id}",
    )
    _approve_change_request(scheduled_change_request, admin_user)
    scheduled_change_request.commit(committed_by=admin_user)
    _approve_change_request(checkout_change_request, admin_user)

    # When
    with capture_audit_logs() as audit_logs:
        with pytest.raises(PrerequisiteHasPrerequisiteError):
            checkout_change_request.commit(committed_by=admin_user)

    # Then
    checkout_change_request.refresh_from_db()
    assert checkout_change_request.committed_at is None
    assert admin_client.get(
        f"/api/v1/environments/{environment_api_key}/features/{checkout.id}/dependencies/",
    ).json() == {"results": []}
    assert list(audit_logs) == []
    assert log.has(
        "dependencies.create_failed",
        level="info",
        organisation__id=organisation,
        project__id=project,
        environment__key=environment_api_key,
        feature__name="checkout",
        prerequisite_feature__name="payments",
    )


# Audit logs


def test_commit_change_request__scheduled_dependency_addition__produces_no_audit_log(
    admin_client: APIClient,
    admin_user: FFAdminUser,
    capture_audit_logs: CaptureAuditLogsFixture,
    create_change_request: CreateChangeRequestFixture,
    environment: int,
    environment_api_key: str,
    log: StructuredLogCapture,
    project: int,
) -> None:
    # Given
    feature = Feature.objects.create(name="checkout", project_id=project)
    prerequisite = Feature.objects.create(name="payments", project_id=project)
    _enable_change_requests(environment)
    change_request = create_change_request(
        feature.id, title="Scheduled", live_from=timezone.now() + timedelta(days=1)
    )
    admin_client.post(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/{prerequisite.id}/?change_request={change_request.id}",
    )
    _approve_change_request(change_request, admin_user)

    # When
    with capture_audit_logs() as audit_logs:
        change_request.commit(committed_by=admin_user)

    # Then
    assert list(audit_logs.values("related_object_type", "log")) == [
        {
            "related_object_type": "CHANGE_REQUEST",
            "log": "Change Request: Scheduled committed",
        },
    ]
    assert admin_client.get(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/",
    ).json() == {"results": []}
    assert not log.has("dependencies.created")


def test_commit_change_request__scheduled_dependency_deletion__produces_no_audit_log(
    add_feature_prerequisite: AddFeaturePrerequisiteFixture,
    admin_client: APIClient,
    admin_user: FFAdminUser,
    capture_audit_logs: CaptureAuditLogsFixture,
    create_change_request: CreateChangeRequestFixture,
    environment: int,
    environment_api_key: str,
    log: StructuredLogCapture,
    project: int,
) -> None:
    # Given
    feature = Feature.objects.create(name="checkout", project_id=project)
    prerequisite = Feature.objects.create(name="payments", project_id=project)
    live_dependency = add_feature_prerequisite(
        environment_api_key, feature.id, prerequisite.id
    )
    _enable_change_requests(environment)
    change_request = create_change_request(
        feature.id, title="Scheduled", live_from=timezone.now() + timedelta(days=1)
    )
    admin_client.delete(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/{prerequisite.id}/?change_request={change_request.id}",
    )
    _approve_change_request(change_request, admin_user)

    # When
    with capture_audit_logs() as audit_logs:
        change_request.commit(committed_by=admin_user)

    # Then
    assert list(audit_logs.values("related_object_type", "log")) == [
        {
            "related_object_type": "CHANGE_REQUEST",
            "log": "Change Request: Scheduled committed",
        },
    ]
    assert admin_client.get(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/",
    ).json() == {"results": [live_dependency]}
    assert not log.has("dependencies.deleted")


def test_commit_change_request__dependency_addition_live_now__produces_audit_log(
    admin_client: APIClient,
    admin_user: FFAdminUser,
    capture_audit_logs: CaptureAuditLogsFixture,
    create_change_request: CreateChangeRequestFixture,
    environment: int,
    environment_api_key: str,
    log: StructuredLogCapture,
    organisation: int,
    project: int,
) -> None:
    # Given
    feature = Feature.objects.create(name="checkout", project_id=project)
    prerequisite = Feature.objects.create(name="payments", project_id=project)
    _enable_change_requests(environment)
    change_request = create_change_request(feature.id, title="Live now")
    staged_dependency = admin_client.post(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/{prerequisite.id}/?change_request={change_request.id}",
    ).json()
    _approve_change_request(change_request, admin_user)

    # When
    with capture_audit_logs() as audit_logs:
        change_request.commit(committed_by=admin_user)

    # Then
    assert list(audit_logs.order_by("id").values("related_object_type", "log")) == [
        {
            "related_object_type": "EF_VERSION",
            "log": "New version published for feature: checkout",
        },
        {
            "related_object_type": "FEATURE",
            "log": "Feature 'payments' added as a dependency for feature 'checkout'.",
        },
        {
            "related_object_type": "CHANGE_REQUEST",
            "log": "Change Request: Live now committed",
        },
    ]
    assert admin_client.get(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/",
    ).json() == {"results": [staged_dependency]}
    assert log.has(
        "dependencies.created",
        level="info",
        organisation__id=organisation,
        project__id=project,
        environment__key=environment_api_key,
        feature__name="checkout",
        prerequisite_feature__name="payments",
    )


def test_commit_change_request__dependency_deletion_live_now__produces_audit_log(
    add_feature_prerequisite: AddFeaturePrerequisiteFixture,
    admin_client: APIClient,
    admin_user: FFAdminUser,
    capture_audit_logs: CaptureAuditLogsFixture,
    create_change_request: CreateChangeRequestFixture,
    environment: int,
    environment_api_key: str,
    log: StructuredLogCapture,
    organisation: int,
    project: int,
) -> None:
    # Given
    feature = Feature.objects.create(name="checkout", project_id=project)
    prerequisite = Feature.objects.create(name="payments", project_id=project)
    add_feature_prerequisite(environment_api_key, feature.id, prerequisite.id)
    _enable_change_requests(environment)
    change_request = create_change_request(feature.id, title="Live now")
    admin_client.delete(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/{prerequisite.id}/?change_request={change_request.id}",
    )
    _approve_change_request(change_request, admin_user)

    # When
    with capture_audit_logs() as audit_logs:
        change_request.commit(committed_by=admin_user)

    # Then
    assert list(audit_logs.order_by("id").values("related_object_type", "log")) == [
        {
            "related_object_type": "EF_VERSION",
            "log": "New version published for feature: checkout",
        },
        {
            "related_object_type": "FEATURE",
            "log": "Feature 'payments' removed as a dependency for feature 'checkout'.",
        },
        {
            "related_object_type": "CHANGE_REQUEST",
            "log": "Change Request: Live now committed",
        },
    ]
    assert admin_client.get(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/",
    ).json() == {"results": []}
    assert log.has(
        "dependencies.deleted",
        level="info",
        organisation__id=organisation,
        project__id=project,
        environment__key=environment_api_key,
        feature__name="checkout",
        prerequisite_feature__name="payments",
    )


def test_publish_change_request__dependency_addition_going_live__produces_audit_log(
    admin_client: APIClient,
    admin_user: FFAdminUser,
    capture_audit_logs: CaptureAuditLogsFixture,
    create_change_request: CreateChangeRequestFixture,
    environment: int,
    environment_api_key: str,
    freezer: FrozenDateTimeFactory,
    log: StructuredLogCapture,
    organisation: int,
    project: int,
) -> None:
    # Given
    feature = Feature.objects.create(name="checkout", project_id=project)
    prerequisite = Feature.objects.create(name="payments", project_id=project)
    _enable_change_requests(environment)
    live_from = timezone.now() + timedelta(days=1)
    change_request = create_change_request(
        feature.id, title="Scheduled", live_from=live_from
    )
    staged_dependency = admin_client.post(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/{prerequisite.id}/?change_request={change_request.id}",
    ).json()
    _approve_change_request(change_request, admin_user)
    change_request.commit(committed_by=admin_user)
    freezer.move_to(live_from)

    # When
    with capture_audit_logs() as audit_logs:
        publish_version_change_set(
            version_change_set_id=change_request.change_sets.get().id,
            user_id=admin_user.id,
            is_scheduled=True,
        )

    # Then
    assert list(audit_logs.order_by("id").values("related_object_type", "log")) == [
        {
            "related_object_type": "EF_VERSION",
            "log": "New version published for feature: checkout",
        },
        {
            "related_object_type": "FEATURE",
            "log": "Feature 'payments' added as a dependency for feature 'checkout'.",
        },
    ]
    assert admin_client.get(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/",
    ).json() == {"results": [staged_dependency]}
    assert log.has(
        "dependencies.created",
        level="info",
        organisation__id=organisation,
        project__id=project,
        environment__key=environment_api_key,
        feature__name="checkout",
        prerequisite_feature__name="payments",
    )


def test_publish_change_request__dependency_deletion_going_live__produces_audit_log(
    add_feature_prerequisite: AddFeaturePrerequisiteFixture,
    admin_client: APIClient,
    admin_user: FFAdminUser,
    capture_audit_logs: CaptureAuditLogsFixture,
    create_change_request: CreateChangeRequestFixture,
    environment: int,
    environment_api_key: str,
    freezer: FrozenDateTimeFactory,
    log: StructuredLogCapture,
    organisation: int,
    project: int,
) -> None:
    # Given
    feature = Feature.objects.create(name="checkout", project_id=project)
    prerequisite = Feature.objects.create(name="payments", project_id=project)
    freezer.tick()
    add_feature_prerequisite(environment_api_key, feature.id, prerequisite.id)
    _enable_change_requests(environment)
    live_from = timezone.now() + timedelta(days=1)
    change_request = create_change_request(
        feature.id, title="Scheduled", live_from=live_from
    )
    admin_client.delete(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/{prerequisite.id}/?change_request={change_request.id}",
    )
    _approve_change_request(change_request, admin_user)
    change_request.commit(committed_by=admin_user)
    freezer.move_to(live_from)

    # When
    with capture_audit_logs() as audit_logs:
        publish_version_change_set(
            version_change_set_id=change_request.change_sets.get().id,
            user_id=admin_user.id,
            is_scheduled=True,
        )

    # Then
    assert list(audit_logs.order_by("id").values("related_object_type", "log")) == [
        {
            "related_object_type": "EF_VERSION",
            "log": "New version published for feature: checkout",
        },
        {
            "related_object_type": "FEATURE",
            "log": "Feature 'payments' removed as a dependency for feature 'checkout'.",
        },
    ]
    assert admin_client.get(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/",
    ).json() == {"results": []}
    assert log.has(
        "dependencies.deleted",
        level="info",
        organisation__id=organisation,
        project__id=project,
        environment__key=environment_api_key,
        feature__name="checkout",
        prerequisite_feature__name="payments",
    )
