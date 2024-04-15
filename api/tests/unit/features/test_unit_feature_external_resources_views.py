import pytest
import simplejson as json
from django.core.serializers.json import DjangoJSONEncoder
from django.db import IntegrityError
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from features.feature_external_resources.models import FeatureExternalResource
from features.models import Feature

_django_json_encoder_default = DjangoJSONEncoder().default


def test_create_feature_external_resource(
    admin_client: APIClient,
    feature: Feature,
) -> None:
    # Given
    feature_external_resource_data = {
        "type": "GITHUB_ISSUE",
        "url": "https://example.com?item=create",
        "feature": feature.id,
        "metadata": {"status": "open"},
    }
    url = reverse("api-v1:features:external-resources-list", args=[feature.id])

    # When
    response = admin_client.post(
        url, data=feature_external_resource_data, format="json"
    )
    # Then
    assert response.status_code == status.HTTP_201_CREATED
    # assert that the payload has been save to the database
    db_record = FeatureExternalResource.objects.filter(
        feature=feature,
        type=feature_external_resource_data["type"],
        url=feature_external_resource_data["url"],
    ).all()

    assert len(db_record) == 1
    assert db_record[0].metadata == json.dumps(
        feature_external_resource_data["metadata"], default=_django_json_encoder_default
    )
    assert db_record[0].feature == feature
    assert db_record[0].type == feature_external_resource_data["type"]
    assert db_record[0].url == feature_external_resource_data["url"]

    # And When
    url = reverse(
        "api-v1:features:external-resources-list",
        kwargs={"feature_pk": feature.id},
    )

    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["count"] == 1
    assert (
        response.json()["results"][0]["type"] == feature_external_resource_data["type"]
    )
    assert response.json()["results"][0]["url"] == feature_external_resource_data["url"]
    assert (
        response.json()["results"][0]["metadata"]
        == feature_external_resource_data["metadata"]
    )


def test_cannot_create_feature_external_resource_when_the_type_is_incorrect(
    admin_client: APIClient,
    feature: Feature,
) -> None:
    # Given
    feature_external_resource_data = {
        "type": "UNKNOWN_TYPE",
        "url": "https://example.com",
        "feature": feature.id,
    }
    url = reverse("api-v1:features:external-resources-list", args=[feature.id])

    # When
    response = admin_client.post(url, data=feature_external_resource_data)
    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_cannot_create_feature_external_resource_due_to_unique_constraint(
    admin_client: APIClient,
    feature: Feature,
    feature_external_resource: FeatureExternalResource,
) -> None:
    # Given
    feature_external_resource_data = {
        "type": "GITHUB_ISSUE",
        "url": "https://github.com/userexample/example-project-repo/issues/11",
        "feature": feature.id,
    }
    url = reverse("api-v1:features:external-resources-list", args=[feature.id])

    # When
    with pytest.raises(IntegrityError) as exc_info:
        response = admin_client.post(url, data=feature_external_resource_data)

        # Then
        assert "duplicate key value violates unique constraint" in str(exc_info.value)
        assert (
            "Key (feature_id, url)=(1, https://github.com/userexample/example-project-repo/issues/11) already exists."
            in str(exc_info.value)
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_delete_feature_external_resource(
    admin_client: APIClient,
    feature_external_resource: FeatureExternalResource,
    feature: Feature,
) -> None:
    # Given
    url = reverse(
        "api-v1:features:external-resources-detail",
        args=[feature.id, feature_external_resource.id],
    )

    # When
    response = admin_client.delete(url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not FeatureExternalResource.objects.filter(
        id=feature_external_resource.id
    ).exists()


def test_get_feature_external_resources(
    admin_client: APIClient,
    feature_external_resource: FeatureExternalResource,
    feature: Feature,
) -> None:
    # Given
    url = reverse(
        "api-v1:features:external-resources-list",
        kwargs={"feature_pk": feature.id},
    )

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK


def test_get_feature_external_resource(
    admin_client: APIClient,
    feature_external_resource: FeatureExternalResource,
    feature: Feature,
) -> None:
    # Given
    url = reverse(
        "api-v1:features:external-resources-detail",
        args=[feature.id, feature_external_resource.id],
    )

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.data["id"] == feature_external_resource.id
    assert response.data["type"] == feature_external_resource.type
    assert response.data["url"] == feature_external_resource.url
