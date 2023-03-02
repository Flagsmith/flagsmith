from django.urls import reverse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from edge_api.identities.views import EdgeIdentityViewSet
from environments.permissions.constants import (
    MANAGE_IDENTITIES,
    VIEW_IDENTITIES,
)
from environments.permissions.permissions import NestedEnvironmentPermissions


def test_edge_identity_view_set_get_permissions():
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
        "perform_destroy": MANAGE_IDENTITIES,
        "get_traits": VIEW_IDENTITIES,
        "update_traits": MANAGE_IDENTITIES,
    }


def test_user_with_manage_identity_permission_can_delete_identity(
    dynamo_enabled_project_environment_one,
    identity_document_without_fs,
    edge_identity_dynamo_wrapper_mock,
    test_user_client,
    view_environment_permission,
    view_identities_permission,
    view_project_permission,
    user_environment_permission,
    user_project_permission,
):
    # Given
    user_environment_permission.permissions.add(
        view_environment_permission, view_identities_permission
    )
    user_project_permission.permissions.add(view_project_permission)

    identity_uuid = identity_document_without_fs["identity_uuid"]

    url = reverse(
        "api-v1:environments:environment-edge-identities-detail",
        args=[dynamo_enabled_project_environment_one.api_key, identity_uuid],
    )

    edge_identity_dynamo_wrapper_mock.get_item_from_uuid_or_404.return_value = (
        identity_document_without_fs
    )

    # When
    response = test_user_client.delete(url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT

    edge_identity_dynamo_wrapper_mock.get_item_from_uuid_or_404.assert_called_with(
        identity_uuid
    )
    edge_identity_dynamo_wrapper_mock.delete_item.assert_called_with(
        identity_document_without_fs["composite_key"]
    )
