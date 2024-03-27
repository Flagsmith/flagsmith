import json
from itertools import chain

from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from metadata.models import (
    MetadataField,
    MetadataModelField,
    MetadataModelFieldRequirement,
)
from metadata.views import SUPPORTED_REQUIREMENTS_MAPPING
from organisations.models import Organisation
from projects.models import Project


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


def test_can_delete_metadata_field(admin_client, a_metadata_field):
    # Given
    url = reverse("api-v1:metadata:metadata-fields-detail", args=[a_metadata_field.id])

    # When
    response = admin_client.delete(url, content_type="application/json")

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_can_update_metadata_field(admin_client, a_metadata_field, organisation):
    # Given
    url = reverse("api-v1:metadata:metadata-fields-detail", args=[a_metadata_field.id])

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


def test_list_metadata_fields(admin_client, a_metadata_field):
    # Given
    base_url = reverse("api-v1:metadata:metadata-fields-list")

    url = f"{base_url}?organisation={a_metadata_field.organisation.id}"

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 1
    assert response.json()["results"][0]["id"] == a_metadata_field.id


def test_list_metadata_fields_without_organisation_returns_400(
    admin_client, a_metadata_field
):
    # Given
    url = reverse("api-v1:metadata:metadata-fields-list")

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_retrieve_metadata_fields(admin_client, a_metadata_field):
    # Given
    url = reverse("api-v1:metadata:metadata-fields-detail", args=[a_metadata_field.id])

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == a_metadata_field.id


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


def test_list_model_metadata_fields(
    required_a_environment_metadata_field,
    optional_b_environment_metadata_field,
    admin_client,
    organisation,
):
    # Given
    url = reverse(
        "api-v1:organisations:metadata-model-fields-list", args=[organisation.id]
    )

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 2


def test_list_model_metadata_fields_content_type_filter(
    required_a_environment_metadata_field,
    optional_b_environment_metadata_field,
    admin_client,
    project,
    a_metadata_field,
    organisation,
):
    # Given - a project metadata field
    project_content_type = ContentType.objects.get_for_model(project)
    a_metadata_project_field = MetadataModelField.objects.create(
        field=a_metadata_field,
        content_type=project_content_type,
    )

    base_url = reverse(
        "api-v1:organisations:metadata-model-fields-list", args=[organisation.id]
    )
    url = f"{base_url}?content_type={project_content_type.id}"

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 1
    assert response.json()["results"][0]["id"] == a_metadata_project_field.id


def test_delete_model_metadata_field(
    environment,
    admin_client,
    a_metadata_field,
    required_a_environment_metadata_field,
    organisation,
):
    # Given
    url = reverse(
        "api-v1:organisations:metadata-model-fields-detail",
        args=[organisation.id, required_a_environment_metadata_field.id],
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
    organisation,
):
    # Given
    url = reverse(
        "api-v1:organisations:metadata-model-fields-detail",
        args=[organisation.id, environment_metadata_field_different_org.id],
    )
    # When
    response = admin_client.delete(url)

    # Then
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_model_metadata_field(
    environment,
    admin_client,
    a_metadata_field,
    required_a_environment_metadata_field,
    organisation,
    environment_content_type,
):
    # Given
    url = reverse(
        "api-v1:organisations:metadata-model-fields-detail",
        args=[organisation.id, required_a_environment_metadata_field.id],
    )
    data = {
        "field": a_metadata_field.id,
        "is_required_for": [],
        "model_name": "environment",
        "content_type": environment_content_type.id,
    }

    # When
    response = admin_client.put(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["field"] == a_metadata_field.id
    assert response.json()["id"] == required_a_environment_metadata_field.id
    assert response.json()["is_required_for"] == []
    assert (
        MetadataModelFieldRequirement.objects.filter(
            model_field=required_a_environment_metadata_field
        ).count()
        == 0
    )


def test_can_not_update_model_metadata_field_from_other_organisation(
    environment, admin_client, environment_metadata_field_different_org, organisation
):
    # Given
    url = reverse(
        "api-v1:organisations:metadata-model-fields-detail",
        args=[organisation.id, environment_metadata_field_different_org.id],
    )
    data = {
        "field": environment_metadata_field_different_org.field.id,
        "is_required": False,
    }

    # When
    response = admin_client.put(url, data=data)

    # Then
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_create_model_metadata_field_for_environments(
    admin_client: APIClient,
    a_metadata_field: MetadataField,
    organisation: Organisation,
    project_content_type: ContentType,
    environment_content_type: ContentType,
    project: Project,
) -> None:
    # Given
    url = reverse(
        "api-v1:organisations:metadata-model-fields-list", args=[organisation.id]
    )
    data = {
        "field": a_metadata_field.id,
        "is_required_for": [
            {"content_type": project_content_type.id, "object_id": project.id}
        ],
        "content_type": environment_content_type.id,
    }

    # When
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )
    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["field"] == a_metadata_field.id
    assert response.json()["is_required_for"][0] == {
        "content_type": project_content_type.id,
        "object_id": project.id,
    }


def test_create_model_metadata_field_for_features(
    admin_client: APIClient,
    a_metadata_field: MetadataField,
    organisation: Organisation,
    project_content_type: ContentType,
    feature_content_type: ContentType,
    project: Project,
) -> None:
    # Given
    url = reverse(
        "api-v1:organisations:metadata-model-fields-list", args=[organisation.id]
    )
    data = {
        "field": a_metadata_field.id,
        "is_required_for": [
            {"content_type": project_content_type.id, "object_id": project.id}
        ],
        "content_type": feature_content_type.id,
    }

    # When
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )
    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["field"] == a_metadata_field.id
    assert response.json()["is_required_for"][0] == {
        "content_type": project_content_type.id,
        "object_id": project.id,
    }


def test_create_model_metadata_field_for_segments(
    admin_client: APIClient,
    a_metadata_field: MetadataField,
    organisation: Organisation,
    project_content_type: ContentType,
    segment_content_type: ContentType,
    project: Project,
) -> None:
    # Given
    url = reverse(
        "api-v1:organisations:metadata-model-fields-list", args=[organisation.id]
    )
    data = {
        "field": a_metadata_field.id,
        "is_required_for": [
            {"content_type": project_content_type.id, "object_id": project.id}
        ],
        "content_type": segment_content_type.id,
    }

    # When
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )
    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["field"] == a_metadata_field.id
    assert response.json()["is_required_for"][0] == {
        "content_type": project_content_type.id,
        "object_id": project.id,
    }


def test_can_not_create_model_metadata_field_using_field_from_other_organisation(
    admin_client, environment_metadata_field_different_org, organisation, project
):
    # Given
    url = reverse(
        "api-v1:organisations:metadata-model-fields-list", args=[organisation.id]
    )
    project_content_type = ContentType.objects.get_for_model(project)
    data = {
        "field": environment_metadata_field_different_org.field.id,
        "is_required": True,
        "content_type": project_content_type.id,
    }

    # When
    response = admin_client.post(url, data=data)

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_supported_content_type(
    admin_client: APIClient, organisation: Organisation
):
    # Given
    url = reverse(
        "api-v1:organisations:metadata-model-fields-supported-content-types",
        args=[organisation.id],
    )

    supported_models = list(
        chain.from_iterable(
            (key, *value) for key, value in SUPPORTED_REQUIREMENTS_MAPPING.items()
        )
    )

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK

    response_models = set(content_type["model"] for content_type in response.json())

    for model in response_models:
        assert model in supported_models


def test_get_supported_required_for_models(admin_client, organisation):
    # Given
    base_url = reverse(
        "api-v1:organisations:metadata-model-fields-supported-required-for-models",
        args=[organisation.id],
    )
    url = f"{base_url}?model_name=environment"

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 2
    assert response.json()[0]["model"] == "organisation"
    assert response.json()[1]["model"] == "project"
