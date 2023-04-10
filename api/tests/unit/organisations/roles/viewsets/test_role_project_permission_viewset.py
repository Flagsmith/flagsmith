import json

from django.urls import reverse
from rest_framework import status

from projects.permissions import CREATE_ENVIRONMENT, VIEW_PROJECT


def test_create_project_permssion_for_role(admin_client, role, project, organisation):
    # Given
    url = reverse(
        "api-v1:organisations:roles-projects-permissions-list",
        args=[organisation.id, role.id],
    )
    data = {
        "project": project.id,
        "permissions": [VIEW_PROJECT],
    }

    # When
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert response.data["role"] == role.id
    assert response.data["project"] == project.id
    assert response.data["permissions"] == [VIEW_PROJECT]
    assert response.data["admin"] is False


def test_list_project_permission_for_role(
    admin_client, role, project, organisation, role_project_permission
):
    # Given
    base_url = reverse(
        "api-v1:organisations:roles-projects-permissions-list",
        args=[organisation.id, role.id],
    )

    url = f"{base_url}?project={project.id}"

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.data["results"][0]["role"] == role.id
    assert response.data["results"][0]["project"] == project.id
    assert response.data["results"][0]["permissions"] == []
    assert response.data["results"][0]["admin"] is False


def test_retrieve_project_permission_for_role(
    admin_client, role, project, organisation, role_project_permission
):
    # Given
    url = reverse(
        "api-v1:organisations:roles-projects-permissions-detail",
        args=[
            organisation.id,
            role.id,
            role_project_permission.id,
        ],
    )

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.data["role"] == role.id
    assert response.data["project"] == project.id
    assert response.data["permissions"] == []
    assert response.data["admin"] is False


def test_update_project_permssion_for_role(
    admin_client, role, project, organisation, role_project_permission
):
    # Given
    url = reverse(
        "api-v1:organisations:roles-projects-permissions-detail",
        args=[organisation.id, role.id, role_project_permission.id],
    )
    data = {
        "project": project.id,
        "permissions": [VIEW_PROJECT, CREATE_ENVIRONMENT],
    }

    # When
    response = admin_client.put(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.data["role"] == role.id
    assert response.data["project"] == project.id
    assert set(response.data["permissions"]) == {VIEW_PROJECT, CREATE_ENVIRONMENT}
    assert response.data["admin"] is False


def test_delete_project_permssion_for_role(
    admin_client, role, project, organisation, role_project_permission
):
    # Given
    url = reverse(
        "api-v1:organisations:roles-projects-permissions-detail",
        args=[organisation.id, role.id, role_project_permission.id],
    )

    # When
    response = admin_client.delete(url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_create_project_permission_for_role_with_project_from_different_organisation_returns_400(
    admin_client,
    role,
    project,
    organisation,
    organisation_two_project_one,
):
    # Given
    url = reverse(
        "api-v1:organisations:roles-projects-permissions-list",
        args=[organisation.id, role.id],
    )
    data = {
        "project": organisation_two_project_one.id,
        "permissions": [VIEW_PROJECT],
    }

    # When
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    assert (
        response.json()["project"][0] == "Project does not belong to this organisation"
    )
