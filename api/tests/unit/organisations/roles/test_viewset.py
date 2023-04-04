import json

from django.urls import reverse
from rest_framework import status


def test_create_role(organisation, admin_client):
    # Given
    url = reverse(
        "api-v1:organisations:organisation-roles-list",
        args=[organisation.id],
    )
    data = {
        "name": "a role",
        "organisation": organisation.id,
    }

    # When
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["name"] == "a role"
    assert response.json()["organisation"] == organisation.id
    assert response.json()["id"]


def test_list_roles(organisation, admin_client, role):
    # Given
    url = reverse(
        "api-v1:organisations:organisation-roles-list",
        args=[organisation.id],
    )
    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["results"][0]["name"] == role.name
    assert len(response.json()["results"]) == 1


def test_retrieve_roles(organisation, admin_client, role):
    # Given
    url = reverse(
        "api-v1:organisations:organisation-roles-detail",
        args=[organisation.id, role.id],
    )
    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == role.name


def test_update_role_name(organisation, admin_client, role):
    # Given
    url = reverse(
        "api-v1:organisations:organisation-roles-detail",
        args=[organisation.id, role.id],
    )
    new_name = "new role name"
    data = {"name": new_name, "organisation": organisation.id}

    # When
    response = admin_client.put(url, data=data)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == new_name


def test_delete_role(organisation, admin_client, role):
    # Given
    url = reverse(
        "api-v1:organisations:organisation-roles-detail",
        args=[organisation.id, role.id],
    )

    # When
    response = admin_client.delete(url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_create_user_role(organisation, admin_client, role, test_user):
    # Given
    url = reverse(
        "api-v1:organisations:user-roles-list",
        args=[organisation.id, role.id],
    )
    data = {"user": test_user.id, "role": role.id}

    # When
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["user"] == test_user.id
    assert response.json()["role"] == role.id
    assert response.json()["id"]


def test_retrieve_user_role(organisation, admin_client, role, user_role, test_user):
    # Given
    url = reverse(
        "api-v1:organisations:user-roles-detail",
        args=[organisation.id, role.id, user_role.id],
    )

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["user"] == test_user.id
    assert response.json()["role"] == role.id
    assert response.json()["id"] == user_role.id


def test_delete_user_role(organisation, admin_client, role, user_role):
    # Given
    url = reverse(
        "api-v1:organisations:user-roles-detail",
        args=[organisation.id, role.id, user_role.id],
    )

    # When
    response = admin_client.delete(url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_list_user_role(organisation, admin_client, role, user_role):
    # Given
    url = reverse(
        "api-v1:organisations:user-roles-list",
        args=[organisation.id, role.id],
    )

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["results"][0]["user"] == user_role.user.id
    assert response.json()["results"][0]["role"] == user_role.role.id


def test_update_user_role(organisation, admin_client, role, user_role, admin_user):
    # Given
    url = reverse(
        "api-v1:organisations:user-roles-detail",
        args=[organisation.id, role.id, user_role.id],
    )
    data = {"role": role.id, "user": admin_user.id}

    # When
    response = admin_client.put(url, data=data)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["user"] == admin_user.id


def test_create_group_role(
    organisation, admin_client, role, default_user_permission_group
):
    # Given
    url = reverse(
        "api-v1:organisations:group-roles-list",
        args=[organisation.id, role.id],
    )
    data = {"group": default_user_permission_group.id, "role": role.id}

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

    data = {"group": default_user_permission_group.id, "role": role.id}

    # When
    response = admin_client.patch(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["group"] == default_user_permission_group.id
    assert response.json()["role"] == role.id
    assert response.json()["id"] == group_role.id
