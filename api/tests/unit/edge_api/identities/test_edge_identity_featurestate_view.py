from typing import Any
from unittest.mock import MagicMock

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from environments.models import Environment
from environments.permissions.models import UserEnvironmentPermission
from features.models import Feature
from permissions.models import PermissionModel


def test_user_with_view_environment_permission_can_retrieve_all_feature_states_for_edge_identity(
    staff_client: APIClient,
    environment: Environment,
    feature: Feature,
    view_environment_permission: PermissionModel,
    user_environment_permission: UserEnvironmentPermission,
    identity_document_without_fs: dict[str, Any],
    edge_identity_dynamo_wrapper_mock: MagicMock,
) -> None:
    # Given
    edge_identity_dynamo_wrapper_mock.get_item_from_uuid_or_404.return_value = (
        identity_document_without_fs
    )
    user_environment_permission.permissions.add(view_environment_permission)
    url = reverse(
        "api-v1:environments:edge-identity-featurestates-all",
        args=(environment.api_key, identity_document_without_fs["identity_uuid"]),
    )

    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1
