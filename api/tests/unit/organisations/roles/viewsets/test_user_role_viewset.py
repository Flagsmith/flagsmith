import json

from django.urls import reverse
from rest_framework import status

from organisations.models import OrganisationRole


def test_create_user_role(organisation, admin_client, role, admin_user):
    # Given
    url = reverse(
        "api-v1:organisations:user-roles-list",
        args=[organisation.id, role.id],
    )
    data = {"user": admin_user.id}

    # When
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["user"] == admin_user.id
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
    data = {"user": admin_user.id}

    # When
    response = admin_client.put(url, data=data)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["user"] == admin_user.id


def test_create_user_role_returns_403_when_user_is_not_admin(
    organisation, test_user_client, role, test_user
):
    # Given
    test_user.add_organisation(organisation, role=OrganisationRole.USER)
    url = reverse(
        "api-v1:organisations:user-roles-list",
        args=[organisation.id, role.id],
    )
    data = {"user": test_user.id}

    # When
    response = test_user_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_user_role_returns_400_for_user_in_different_organisation(
    organisation,
    admin_client,
    role,
    test_user,
    organisation_two,
    django_user_model,
):
    # Given
    # Create a user in another organisation
    other_user = django_user_model.objects.create(username="other_user")
    other_user.add_organisation(organisation_two, role=OrganisationRole.ADMIN)

    url = reverse(
        "api-v1:organisations:user-roles-list",
        args=[organisation.id, role.id],
    )
    data = {"user": other_user.id}

    # When
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )
    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["user"][0] == "User does not belong to this organisation"
