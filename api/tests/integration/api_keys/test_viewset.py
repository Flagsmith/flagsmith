from django.urls import reverse
from rest_framework import status


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


def test_delete_master_api_key(admin_client, organisation, master_api_key_prefix):
    # Given
    url = reverse(
        "api-v1:organisations:organisation-master-api-keys-detail",
        args=[organisation, master_api_key_prefix],
    )

    # When
    response = admin_client.delete(url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_list_master_api_keys(admin_client, organisation, master_api_key_prefix):
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
    assert response.json()["results"][0]["prefix"] == master_api_key_prefix


def test_retrieve_master_api_key(admin_client, organisation, master_api_key_prefix):
    # Given
    url = reverse(
        "api-v1:organisations:organisation-master-api-keys-detail",
        args=[organisation, master_api_key_prefix],
    )

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["prefix"] == master_api_key_prefix


def test_update_master_api_key(admin_client, organisation, master_api_key_prefix):
    # Given
    url = reverse(
        "api-v1:organisations:organisation-master-api-keys-detail",
        args=[organisation, master_api_key_prefix],
    )
    new_name = "updated_test_key"
    data = {
        "prefix": master_api_key_prefix,
        "revoked": True,
        "organisation": organisation,
        "name": new_name,
    }

    # When
    response = admin_client.put(url, data=data)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["prefix"] == master_api_key_prefix
    assert response.json()["revoked"] is True
    assert response.json()["name"] == new_name


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
