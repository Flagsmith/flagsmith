import pytest
from pytest_structlog import StructuredLogCapture
from rest_framework.test import APIClient

from environments.models import Environment
from features.dependencies.types import DependencyEdge
from features.models import Feature
from features.workflows.core.models import ChangeRequest
from segments.models import Segment
from tests.integration.types import AddFeaturePrerequisiteFixture, GetFeatureFixture
from tests.types import CaptureAuditLogsFixture
from users.models import FFAdminUser


def _enable_change_requests(environment: int) -> None:
    Environment.objects.filter(id=environment).update(
        minimum_change_request_approvals=1,
    )


# Direct dependency changes but change requests are enabled


@pytest.mark.usefixtures("environment_v2_versioning")
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


@pytest.mark.usefixtures("environment_v2_versioning")
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


@pytest.mark.usefixtures("environment_v2_versioning")
def test_add_feature_dependency__point_to_open_change_request__responds_201(
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


@pytest.mark.usefixtures("environment_v2_versioning")
def test_delete_feature_dependency__point_to_open_change_request__responds_204(
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
    assert response.status_code == 204
    assert admin_client.get(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/?change_request={change_request.id}",
    ).json() == {"results": []}
    assert admin_client.get(
        f"/api/v1/environments/{environment_api_key}/features/{feature.id}/dependencies/",
    ).json() == {"results": [live_dependency]}
    assert list(audit_logs) == []
    assert not log.has("dependencies.deleted")


@pytest.mark.usefixtures("environment_v2_versioning")
def test_list_feature_dependencies__point_to_open_change_request__responds_200(
    add_feature_prerequisite: AddFeaturePrerequisiteFixture,
    admin_client: APIClient,
    admin_user: FFAdminUser,
    capture_audit_logs: CaptureAuditLogsFixture,
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
    change_request = ChangeRequest.objects.create(
        environment_id=environment, title="Pending", user=admin_user
    )
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


def test_add_feature_dependency__point_to_approved_change_request__responds_400() -> (
    None
):
    raise NotImplementedError


def test_delete_feature_dependency__point_to_approved_change_request__responds_400() -> (
    None
):
    raise NotImplementedError


def test_list_feature_dependencies__point_to_approved_change_request__responds_200() -> (
    None
):
    raise NotImplementedError


# Committed change requests


def test_add_feature_dependency__point_to_committed_change_request__responds_400() -> (
    None
):
    raise NotImplementedError


def test_delete_feature_dependency__point_to_committed_change_request__responds_400() -> (
    None
):
    raise NotImplementedError


def test_list_feature_dependencies__point_to_committed_change_request__responds_400() -> (
    None
):
    raise NotImplementedError


# Feature versioning v1


def test_add_feature_dependency__feature_versioning_v1__responds_409() -> None:
    raise NotImplementedError


def test_delete_feature_dependency__feature_versioning_v1__responds_409() -> None:
    raise NotImplementedError


# Lacking permission


def test__add_feature_dependency__lacking_permission__responds_403() -> None:
    raise NotImplementedError


def test__delete_feature_dependency__lacking_permission__responds_403() -> None:
    raise NotImplementedError


# Stage hygiene


def test__delete_feature_dependency__previously_staged__responds_204_undoing_staged() -> (
    None
):
    raise NotImplementedError


def test__add_feature_dependency__previously_staged__responds_400_leaving_one_staged() -> (
    None
):
    raise NotImplementedError


# Cycle prevention


def test__add_feature_dependency__cycle_on_live_dependencies__responds_400() -> None:
    raise NotImplementedError


def test__add_feature_dependency__cycle_on_scheduled_dependencies__responds_400() -> (
    None
):
    raise NotImplementedError


# Audit logs


def test_commit_change_request__scheduled_dependency_addition__produces_no_audit_log() -> (
    None
):
    raise NotImplementedError


def test_commit_change_request__scheduled_dependency_deletion__produces_no_audit_log() -> (
    None
):
    raise NotImplementedError


def test_commit_change_request__dependency_addition_live_now__produces_audit_log() -> (
    None
):
    raise NotImplementedError


def test_commit_change_request__dependency_deletion_live_now__produces_audit_log() -> (
    None
):
    raise NotImplementedError


def test_publish_change_request__dependency_addition_going_live__produces_audit_log() -> (
    None
):
    raise NotImplementedError


def test_publish_change_request__dependency_deletion_going_live__produces_audit_log() -> (
    None
):
    raise NotImplementedError
