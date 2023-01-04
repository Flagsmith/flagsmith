"""
NOTE: instead of testing MetaDataViewMixin directly by mocking all the other attributes/methods we
test the functionality by testing the viewsets that use it, i.e: EnvironmentViewSet

"""

from django.urls import reverse
from rest_framework import status


def test_get_model_metadata_fields(
    required_a_environment_metadata_field,
    optional_b_environment_metadata_field,
    admin_client,
):
    # Given
    url = reverse("api-v1:environments:environment-get-model-metadata-fields")

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 2


def test_get_model_metadata_fields_only_return_fields_from_orgs_that_user_is_part_of(
    required_a_environment_metadata_field,
    optional_b_environment_metadata_field,
    environment_metadata_field_different_org,
    admin_client,
    environment,
):
    # Given
    url = reverse("api-v1:environments:environment-get-model-metadata-fields")

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 2

    # and the metadata model field for the other organisation is not returned
    assert environment_metadata_field_different_org.id not in [
        m["id"] for m in response.json()
    ]


def test_create_model_metadata_field(admin_client, a_metadata_field):
    # Given
    url = reverse("api-v1:environments:environment-create-model-metadata-field")
    data = {
        "field": a_metadata_field.id,
        "is_required": True,
    }

    # When
    response = admin_client.post(url, data=data)

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["field"] == a_metadata_field.id
    assert response.json()["is_required"] is True


def test_can_not_create_model_metadata_field_using_field_from_other_organisation(
    admin_client, environment_metadata_field_different_org
):
    # Given
    url = reverse("api-v1:environments:environment-create-model-metadata-field")
    data = {
        "field": environment_metadata_field_different_org.field.id,
        "is_required": True,
    }

    # When
    response = admin_client.post(url, data=data)

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_update_model_metadata_field(
    environment, admin_client, a_metadata_field, required_a_environment_metadata_field
):
    # Given
    url = reverse(
        "api-v1:environments:environment-update-model-metadata-field",
        args=[required_a_environment_metadata_field.id],
    )
    data = {
        "field": a_metadata_field.id,
        "is_required": False,
    }

    # When
    response = admin_client.put(url, data=data)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["field"] == a_metadata_field.id
    assert response.json()["id"] == required_a_environment_metadata_field.id
    assert response.json()["is_required"] is False


def test_can_not_update_model_metadata_field_from_other_organisation(
    environment,
    admin_client,
    environment_metadata_field_different_org,
):
    # Given
    url = reverse(
        "api-v1:environments:environment-update-model-metadata-field",
        args=[environment_metadata_field_different_org.id],
    )
    data = {
        "field": environment_metadata_field_different_org.field.id,
        "is_required": False,
    }

    # When
    response = admin_client.put(url, data=data)

    # Then
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_model_metadata_field(
    environment, admin_client, a_metadata_field, required_a_environment_metadata_field
):
    # Given
    url = reverse(
        "api-v1:environments:environment-update-model-metadata-field",
        args=[required_a_environment_metadata_field.id],
    )
    # When
    response = admin_client.delete(url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_can_not_delete_model_metadata_field_from_other_organisation(
    environment,
    admin_client,
    a_metadata_field,
    required_a_environment_metadata_field,
    environment_metadata_field_different_org,
):
    # Given
    url = reverse(
        "api-v1:environments:environment-update-model-metadata-field",
        args=[environment_metadata_field_different_org.id],
    )
    # When
    response = admin_client.delete(url)

    # Then
    assert response.status_code == status.HTTP_404_NOT_FOUND
