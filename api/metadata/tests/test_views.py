import json

from django.urls import reverse
from rest_framework import status


def test_can_create_metadata_field(admin_client, organisation):
    # Given
    url = reverse("api-v1:metadata:metadata-fields-list")
    field_name = "some_id"
    field_type = "int"

    data = {"name": field_name, "type": field_type, "organisation": organisation.id}

    # When
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["id"]
    assert response.json()["name"] == field_name
    assert response.json()["type"] == field_type
    assert response.json()["organisation"] == organisation.id


def test_can_delete_metadata_field(admin_client, metadata_field):
    # Given
    url = reverse("api-v1:metadata:metadata-fields-detail", args=[metadata_field.id])

    # When
    response = admin_client.delete(url, content_type="application/json")

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_can_update_metadata_field(admin_client, metadata_field, organisation):
    # Given
    url = reverse("api-v1:metadata:metadata-fields-detail", args=[metadata_field.id])

    new_field_type = "bool"
    new_field_name = "new_field_name"

    data = {
        "name": new_field_name,
        "type": new_field_type,
        "organisation": organisation.id,
    }

    # When
    response = admin_client.put(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["name"] == new_field_name
    assert response.json()["type"] == new_field_type


def test_can_list_metadata_fields(admin_client, metadata_field):
    # Given
    url = reverse("api-v1:metadata:metadata-fields-list")

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 1
    assert response.json()["results"][0]["id"] == metadata_field.id


def test_create_metadata_field_returns_403_for_non_org_admin(
    test_user_client, organisation
):
    url = reverse("api-v1:metadata:metadata-fields-list")
    field_name = "some_id"
    field_type = "int"

    data = {"name": field_name, "type": field_type, "organisation": organisation.id}

    # When
    response = test_user_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN
