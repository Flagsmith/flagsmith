from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from external_resources.models import ExternalResources
from features.models import Feature


def test_create_external_resources(
    admin_client: APIClient,
    feature: Feature,
) -> None:
    # Given
    external_resource_data = {
        "type": "Test External Resource",
        "url": "https://example.com",
        "feature": feature.id,
    }
    url = reverse("api-v1:external-resources-list")
    response = admin_client.post(url, data=external_resource_data)
    # Then
    assert response.status_code == status.HTTP_201_CREATED


def test_delete_external_resources(
    admin_client: APIClient,
    external_resource: ExternalResources,
) -> None:
    url = reverse("api-v1:external-resources-detail", args=[external_resource.id])
    response = admin_client.delete(url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not ExternalResources.objects.filter(id=external_resource.id).exists()


def test_get_external_resources_by_feature(
    admin_client: APIClient,
    external_resource: ExternalResources,
    feature: Feature,
) -> None:
    url = reverse(
        "api-v1:features:get-external-resource-by-feature",
        kwargs={"features_pk": feature.id},
    )
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
