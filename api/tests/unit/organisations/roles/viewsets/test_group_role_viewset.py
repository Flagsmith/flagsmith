import json

from django.urls import reverse
from rest_framework import status

from users.models import UserPermissionGroup


def test_create_group_role(
    organisation, admin_client, role, default_user_permission_group
):
    # Given
    url = reverse(
        "api-v1:organisations:group-roles-list",
        args=[organisation.id, role.id],
    )
    data = {"group": default_user_permission_group.id}

    # When
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )
    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["group"] == default_user_permission_group.id
    assert response.json()["role"] == role.id
    assert response.json()["id"]


def test_delete_group_role(organisation, admin_client, role, group_role):
    # Given
    url = reverse(
        "api-v1:organisations:group-roles-detail",
        args=[organisation.id, role.id, group_role.id],
    )

    # When
    response = admin_client.delete(url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_retrieve_group_role(
    organisation, admin_client, role, user_permission_group, group_role
):
    # Given
    url = reverse(
        "api-v1:organisations:group-roles-detail",
        args=[organisation.id, role.id, group_role.id],
    )

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["group"] == user_permission_group.id
    assert response.json()["role"] == role.id
    assert response.json()["id"] == group_role.id


def test_list_group_role(
    organisation, admin_client, role, group_role, user_permission_group
):
    # Given
    url = reverse(
        "api-v1:organisations:group-roles-list",
        args=[organisation.id, role.id],
    )

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["results"][0]["group"] == user_permission_group.id
    assert response.json()["results"][0]["role"] == role.id
    assert response.json()["results"][0]["id"] == group_role.id


def test_update_group_role(
    organisation,
    admin_client,
    role,
    default_user_permission_group,
    group_role,
):
    # Given
    url = reverse(
        "api-v1:organisations:group-roles-detail",
        args=[organisation.id, role.id, group_role.id],
    )

    data = {"group": default_user_permission_group.id}

    # When
    response = admin_client.patch(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["group"] == default_user_permission_group.id
    assert response.json()["role"] == role.id
    assert response.json()["id"] == group_role.id


def test_create_role_group_returns_400_for_user_group_in_different_organisation(
    organisation, organisation_two, admin_client, role
):
    # Given
    other_user_permission_group = UserPermissionGroup.objects.create(
        name="Other Group", organisation=organisation_two
    )
    url = reverse(
        "api-v1:organisations:group-roles-list",
        args=[organisation.id, role.id],
    )
    data = {"group": other_user_permission_group.id}

    # When
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["group"] == ["Group does not belong to this organisation"]
