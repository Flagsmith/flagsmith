import typing

from common.environments.permissions import (
    MANAGE_IDENTITIES,
    VIEW_ENVIRONMENT,
    VIEW_IDENTITIES,
)
from django.urls import reverse
from pytest_mock import MockerFixture
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.test import APIClient

from edge_api.identities.models import EdgeIdentity
from edge_api.identities.views import EdgeIdentityViewSet
from environments.models import Environment
from environments.permissions.permissions import NestedEnvironmentPermissions
from features.models import Feature
from tests.types import WithEnvironmentPermissionsCallable
from users.models import FFAdminUser

if typing.TYPE_CHECKING:
    from mypy_boto3_dynamodb.service_resource import Table


def test_edge_identity_view_set_get_permissions() -> None:
    # Given
    view_set = EdgeIdentityViewSet()

    # When
    permissions = view_set.get_permissions()

    # Then
    assert isinstance(permissions[0], IsAuthenticated)
    assert isinstance(permissions[1], NestedEnvironmentPermissions)

    assert permissions[1].action_permission_map == {
        "list": VIEW_IDENTITIES,
        "retrieve": VIEW_IDENTITIES,
        "create": MANAGE_IDENTITIES,
        "destroy": MANAGE_IDENTITIES,
        "get_traits": VIEW_IDENTITIES,
        "update_traits": MANAGE_IDENTITIES,
    }


def test_user_with_manage_identity_permission_can_delete_identity(
    environment: Environment,
    identity_document_without_fs: dict[str, typing.Any],
    staff_client: APIClient,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
    flagsmith_identities_table: "Table",
) -> None:
    # Given
    with_environment_permissions(  # type: ignore[call-arg]
        [VIEW_ENVIRONMENT, MANAGE_IDENTITIES, VIEW_IDENTITIES],
        environment.id,
    )

    flagsmith_identities_table.put_item(Item=identity_document_without_fs)
    identity_uuid = identity_document_without_fs["identity_uuid"]
    composite_key = identity_document_without_fs["composite_key"]

    url = reverse(
        "api-v1:environments:environment-edge-identities-detail",
        args=[environment.api_key, identity_uuid],
    )

    # When
    response = staff_client.delete(url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert flagsmith_identities_table.get_item(Key={"composite_key": composite_key})


def test_edge_identity_viewset_returns_404_for_invalid_environment_key(
    admin_client: APIClient,
) -> None:
    # Given
    api_key = "not-valid"
    url = reverse(
        "api-v1:environments:environment-edge-identities-list", args=[api_key]
    )

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_edge_identity_overrides_for_a_feature(
    staff_client: APIClient,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
    mocker: MockerFixture,
    feature: Feature,
    environment: Environment,
    edge_identity_override_document: dict,  # type: ignore[type-arg]
    edge_identity_override_document_2: dict,  # type: ignore[type-arg]
    edge_identity_model: EdgeIdentity,
    edge_identity_model_2: EdgeIdentity,
) -> None:
    # Given
    base_url = reverse(
        "api-v1:environments:edge-identity-overrides", args=[environment.api_key]
    )
    url = f"{base_url}?feature={feature.id}"
    with_environment_permissions([VIEW_IDENTITIES])  # type: ignore[call-arg]

    mock_dynamodb_wrapper = mocker.MagicMock()
    mocker.patch(
        "edge_api.identities.edge_identity_service.ddb_environment_v2_wrapper",
        mock_dynamodb_wrapper,
    )

    mock_dynamodb_wrapper.get_identity_overrides_by_environment_id.return_value = [
        edge_identity_override_document,
        edge_identity_override_document_2,
    ]

    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_json = response.json()
    assert len(response_json["results"]) == 2
    assert response_json["results"][0] == {
        "identity_uuid": edge_identity_model.identity_uuid,
        "identifier": edge_identity_model.identifier,
        "feature_state": {
            "feature_state_value": None,
            "multivariate_feature_state_values": [],
            "featurestate_uuid": edge_identity_override_document["feature_state"][
                "featurestate_uuid"
            ],
            "enabled": True,
            "feature": feature.id,
        },
    }
    assert response_json["results"][1] == {
        "identity_uuid": edge_identity_model_2.identity_uuid,
        "identifier": edge_identity_model_2.identifier,
        "feature_state": {
            "feature_state_value": None,
            "multivariate_feature_state_values": [],
            "featurestate_uuid": edge_identity_override_document_2["feature_state"][
                "featurestate_uuid"
            ],
            "enabled": True,
            "feature": feature.id,
        },
    }

    mock_dynamodb_wrapper.get_identity_overrides_by_environment_id.assert_called_once_with(
        environment_id=environment.id,
        feature_id=feature.id,
    )


def test_user_without_manage_identities_permission_cannot_get_edge_identity_overrides_for_a_feature(
    staff_client: APIClient,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
    feature: Feature,
    environment: Environment,
) -> None:
    # Given
    base_url = reverse(
        "api-v1:environments:edge-identity-overrides", args=[environment.api_key]
    )
    url = f"{base_url}?feature={feature.id}"
    with_environment_permissions([VIEW_ENVIRONMENT])  # type: ignore[call-arg]

    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_user_cannot_delete_identity_from_another_project(
    identity_document_without_fs: dict[str, typing.Any],
    flagsmith_identities_table: "Table",
    environment: Environment,
) -> None:
    # Given
    # A user that belongs to no organisation
    user = FFAdminUser.objects.create(email="no-orgs@example.com")

    assert not user.belongs_to(environment.project.organisation_id)

    api_client = APIClient()
    api_client.force_authenticate(user)

    identifier = identity_document_without_fs["identifier"]
    identity_uuid = identity_document_without_fs["identity_uuid"]
    environment_api_key = environment.api_key
    composite_key = f"{environment_api_key}_{identifier}"

    flagsmith_identities_table.put_item(Item=identity_document_without_fs)

    url = reverse(
        "api-v1:environments:environment-edge-identities-detail",
        args=[environment_api_key, identity_uuid],
    )

    # When
    response = api_client.delete(url)

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN

    assert flagsmith_identities_table.get_item(Key={"composite_key": composite_key})
