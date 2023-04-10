import json

from django.urls import reverse
from rest_framework import status

from organisations.models import OrganisationRole


def test_create_role(organisation, admin_client):
    # Given
    url = reverse(
        "api-v1:organisations:organisation-roles-list",
        args=[organisation.id],
    )
    data = {
        "name": "a role",
    }

    # When
    response = admin_client.post(url, data=data)

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
    data = {"name": new_name}

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


def test_create_role_organisation_id_in_body_is_read_only(
    organisation, admin_client, other_organisation
):
    # Given
    url = reverse(
        "api-v1:organisations:organisation-roles-list",
        args=[organisation.id],
    )
    data = {
        "name": "a role",
        "organisation": other_organisation.id,
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


def test_create_role_returns_403_if_user_is_not_organisation_admin(
    test_user_client, organisation, test_user
):
    # Given
    test_user.add_organisation(organisation, role=OrganisationRole.USER)

    url = reverse(
        "api-v1:organisations:organisation-roles-list",
        args=[organisation.id],
    )
    data = {
        "name": "a role",
    }

    # When
    response = test_user_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN
