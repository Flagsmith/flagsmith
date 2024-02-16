from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from organisations.models import Organisation


def test_create_master_api_key_returns_key_in_response(admin_client, organisation):
    # Given
    url = reverse(
        "api-v1:organisations:organisation-master-api-keys-list",
        args=[organisation],
    )
    data = {"name": "test_key", "organisation": organisation}

    # When
    response = admin_client.post(url, data=data)

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["key"] is not None
    assert response.json()["is_admin"] is True


def test_creating_non_admin_master_api_key_without_rbac_returns_400(
    admin_client, organisation, settings
):
    # Given
    settings.IS_RBAC_INSTALLED = False

    url = reverse(
        "api-v1:organisations:organisation-master-api-keys-list",
        args=[organisation],
    )
    data = {"name": "test_key", "organisation": organisation, "is_admin": False}

    # When
    response = admin_client.post(url, data=data)

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["is_admin"] == [
        "RBAC is not installed, cannot create non-admin key"
    ]


def test_delete_master_api_key(admin_client, organisation, admin_master_api_key_prefix):
    # Given
    url = reverse(
        "api-v1:organisations:organisation-master-api-keys-detail",
        args=[organisation, admin_master_api_key_prefix],
    )

    # When
    response = admin_client.delete(url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_list_master_api_keys(
    admin_client: APIClient,
    organisation: int,
    admin_master_api_key_prefix: str,
) -> None:
    # Given
    url = reverse(
        "api-v1:organisations:organisation-master-api-keys-list",
        args=[organisation],
    )

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["count"] == 1
    assert response.json()["results"][0]["prefix"] == admin_master_api_key_prefix
    assert response.json()["results"][0]["has_expired"] is False


def test_list_master_api_keys__when_expired(
    admin_client: APIClient,
    organisation: Organisation,
    expired_api_key_prefix: str,
) -> None:
    # Given
    url = reverse(
        "api-v1:organisations:organisation-master-api-keys-list",
        args=[organisation],
    )

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["count"] == 1
    assert response.json()["results"][0]["prefix"] == expired_api_key_prefix
    assert response.json()["results"][0]["has_expired"] is True


def test_retrieve_master_api_key(
    admin_client, organisation, admin_master_api_key_prefix
):
    # Given
    url = reverse(
        "api-v1:organisations:organisation-master-api-keys-detail",
        args=[organisation, admin_master_api_key_prefix],
    )

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["prefix"] == admin_master_api_key_prefix


def test_update_master_api_key(
    admin_client, organisation, admin_master_api_key_prefix, settings
):
    # Given
    settings.IS_RBAC_INSTALLED = True

    url = reverse(
        "api-v1:organisations:organisation-master-api-keys-detail",
        args=[organisation, admin_master_api_key_prefix],
    )
    new_name = "updated_test_key"
    data = {
        "prefix": admin_master_api_key_prefix,
        "revoked": True,
        "organisation": organisation,
        "name": new_name,
        "is_admin": False,
    }

    # When
    response = admin_client.put(url, data=data)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["prefix"] == admin_master_api_key_prefix
    assert response.json()["revoked"] is True
    assert response.json()["name"] == new_name
    assert response.json()["is_admin"] is False


def test_update_master_api_key_is_admin_returns_400_if_rbac_is_not_installed(
    admin_client, organisation, admin_master_api_key_prefix, settings
):
    # Given
    settings.IS_RBAC_INSTALLED = False

    url = reverse(
        "api-v1:organisations:organisation-master-api-keys-detail",
        args=[organisation, admin_master_api_key_prefix],
    )
    new_name = "updated_test_key"
    data = {
        "prefix": admin_master_api_key_prefix,
        "organisation": organisation,
        "name": new_name,
        "is_admin": False,
    }

    # When
    response = admin_client.put(url, data=data)

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["is_admin"] == [
        "RBAC is not installed, cannot create non-admin key"
    ]


def test_api_returns_403_if_user_is_not_the_org_admin(non_admin_client, organisation):
    # Given
    url = reverse(
        "api-v1:organisations:organisation-master-api-keys-list",
        args=[organisation],
    )
    # When
    response = non_admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_master_api_key_ignores_organisation_in_body(admin_client, organisation):
    # Given
    list_create_url = reverse(
        "api-v1:organisations:organisation-master-api-keys-list",
        args=[organisation],
    )
    name = "test_key"
    data = {"name": name, "organisation": 999}

    # When
    create_response = admin_client.post(list_create_url, data=data)

    # Then
    assert create_response.status_code == status.HTTP_201_CREATED
    key = create_response.json()["key"]
    assert key is not None

    # and
    # the key exists in the organisation provided in the URL
    list_response = admin_client.get(list_create_url)
    assert list_response.status_code == status.HTTP_200_OK
    list_response_json = list_response.json()
    assert list_response_json["count"] == 1

    assert list_response_json["results"][0]["name"] == name
    assert key.startswith(list_response_json["results"][0]["prefix"])


def test_deleted_api_key_is_not_returned_in_list_and_cannot_be_used(
    admin_client: APIClient,
    organisation: int,
    admin_master_api_key_client: APIClient,
    admin_master_api_key_prefix: str,
) -> None:
    # Given
    # the relevant URLs
    list_url = reverse(
        "api-v1:organisations:organisation-master-api-keys-list",
        args=[organisation],
    )
    detail_url = reverse(
        "api-v1:organisations:organisation-master-api-keys-detail",
        args=[organisation, admin_master_api_key_prefix],
    )
    list_projects_url = "%s?organisation=%s" % (
        reverse("api-v1:projects:project-list"),
        organisation,
    )

    # and we verify that before deletion, the master api key authenticated client
    # can retrieve the projects for the organisation
    valid_response = admin_master_api_key_client.get(list_projects_url)
    assert valid_response.status_code == 200

    # When
    # we delete the api key
    delete_response = admin_client.delete(detail_url)
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT

    # Then
    # It is not returned in the list response
    list_response = admin_client.get(list_url)
    assert list_response.json()["count"] == 0

    # And
    # it cannot be used to authenticate with the API anymore
    invalid_response = admin_master_api_key_client.get(list_projects_url)
    assert invalid_response.status_code == 401
