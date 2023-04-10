import json

from django.urls import reverse
from rest_framework import status

from environments.permissions.constants import (
    UPDATE_FEATURE_STATE,
    VIEW_ENVIRONMENT,
)


def test_create_environment_permission_for_role(
    admin_client, role, environment, organisation
):
    # Given
    url = reverse(
        "api-v1:organisations:roles-environments-permissions-list",
        args=[organisation.id, role.id],
    )
    data = {
        "environment": environment.id,
        "permissions": [VIEW_ENVIRONMENT],
    }

    # When
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["role"] == role.id
    assert response.data["environment"] == environment.id
    assert response.data["permissions"] == [VIEW_ENVIRONMENT]
    assert response.data["admin"] is False


def test_retrieve_environment_permission_for_role(
    admin_client, role, environment, organisation, role_environment_permission
):
    # Given
    url = reverse(
        "api-v1:organisations:roles-environments-permissions-detail",
        args=[organisation.id, role.id, role_environment_permission.id],
    )

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.data["role"] == role.id
    assert response.data["environment"] == environment.id
    assert response.data["permissions"] == []
    assert response.data["admin"] == role_environment_permission.admin


def test_list_environment_permission_for_role(
    admin_client, role, environment, organisation, role_environment_permission
):
    # Given
    base_url = reverse(
        "api-v1:organisations:roles-environments-permissions-list",
        args=[organisation.id, role.id],
    )
    url = f"{base_url}?environment={environment.id}"

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.data["count"] == 1
    assert response.data["results"][0]["role"] == role.id
    assert response.data["results"][0]["environment"] == environment.id
    assert response.data["results"][0]["permissions"] == []
    assert response.data["results"][0]["admin"] == role_environment_permission.admin


def test_update_environment_permission_for_role(
    admin_client, role, environment, organisation, role_environment_permission
):
    # Given
    url = reverse(
        "api-v1:organisations:roles-environments-permissions-detail",
        args=[organisation.id, role.id, role_environment_permission.id],
    )
    data = {
        "environment": environment.id,
        "permissions": [VIEW_ENVIRONMENT, UPDATE_FEATURE_STATE],
    }

    # When
    response = admin_client.put(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.data["role"] == role.id
    assert response.data["environment"] == environment.id
    assert set(response.data["permissions"]) == {VIEW_ENVIRONMENT, UPDATE_FEATURE_STATE}
    assert response.data["admin"] is False


def test_delete_environment_permission_for_role(
    admin_client, role, environment, organisation, role_environment_permission
):
    # Given
    url = reverse(
        "api-v1:organisations:roles-environments-permissions-detail",
        args=[organisation.id, role.id, role_environment_permission.id],
    )

    # When
    response = admin_client.delete(url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_create_environment_permission_for_role_with_environment_from_different_organisation_returns_400(
    admin_client,
    role,
    environment,
    organisation,
    organisation_two_project_one_environment_one,
):
    # Given
    url = reverse(
        "api-v1:organisations:roles-environments-permissions-list",
        args=[organisation.id, role.id],
    )
    data = {
        "environment": organisation_two_project_one_environment_one.id,
        "permissions": [VIEW_ENVIRONMENT],
    }

    # When
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    assert (
        response.json()["environment"][0]
        == "Environment does not belong to this organisation"
    )
