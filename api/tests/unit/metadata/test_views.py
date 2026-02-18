import json
from itertools import chain

import pytest
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from metadata.models import (
    MetadataField,
    MetadataModelField,
    MetadataModelFieldRequirement,
)
from metadata.views import SUPPORTED_REQUIREMENTS_MAPPING  # type: ignore[attr-defined]
from organisations.models import Organisation
from projects.models import Project
from users.models import FFAdminUser


def test_can_create_metadata_field(admin_client, organisation):  # type: ignore[no-untyped-def]
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


def test_can_delete_metadata_field(admin_client, a_metadata_field):  # type: ignore[no-untyped-def]
    # Given
    url = reverse("api-v1:metadata:metadata-fields-detail", args=[a_metadata_field.id])

    # When
    response = admin_client.delete(url, content_type="application/json")

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_can_update_metadata_field(admin_client, a_metadata_field, organisation):  # type: ignore[no-untyped-def]
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


def test_list_metadata_fields(admin_client, a_metadata_field):  # type: ignore[no-untyped-def]
    # Given
    base_url = reverse("api-v1:metadata:metadata-fields-list")

    url = f"{base_url}?organisation={a_metadata_field.organisation.id}"

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 1
    assert response.json()["results"][0]["id"] == a_metadata_field.id


def test_list_metadata_fields_without_organisation_returns_400(  # type: ignore[no-untyped-def]
    admin_client, a_metadata_field
):
    # Given
    url = reverse("api-v1:metadata:metadata-fields-list")

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_retrieve_metadata_fields(admin_client, a_metadata_field):  # type: ignore[no-untyped-def]
    # Given
    url = reverse("api-v1:metadata:metadata-fields-detail", args=[a_metadata_field.id])

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == a_metadata_field.id


def test_create_metadata_field_returns_403_for_non_org_admin(  # type: ignore[no-untyped-def]
    staff_client: APIClient,
    organisation: Organisation,
):
    url = reverse("api-v1:metadata:metadata-fields-list")
    field_name = "some_id"
    field_type = "int"

    data = {"name": field_name, "type": field_type, "organisation": organisation.id}

    # When
    response = staff_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_list_model_metadata_fields(  # type: ignore[no-untyped-def]
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


def test_list_model_metadata_fields_content_type_filter(  # type: ignore[no-untyped-def]
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


def test_delete_model_metadata_field(  # type: ignore[no-untyped-def]
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


def test_can_not_delete_model_metadata_field_from_other_organisation(  # type: ignore[no-untyped-def]
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


def test_update_model_metadata_field(  # type: ignore[no-untyped-def]
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


def test_can_not_update_model_metadata_field_from_other_organisation(  # type: ignore[no-untyped-def]
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


def test_can_not_create_model_metadata_field_using_field_from_other_organisation(  # type: ignore[no-untyped-def]
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


def test_get_supported_content_type(  # type: ignore[no-untyped-def]
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


def test_get_supported_required_for_models(admin_client, organisation):  # type: ignore[no-untyped-def]
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


def test_create_metadata_field__with_project__returns_201(
    admin_client: APIClient,
    organisation: Organisation,
    project: Project,
) -> None:
    # Given
    url = reverse("api-v1:metadata:metadata-fields-list")
    data = {
        "name": "project_field",
        "type": "str",
        "organisation": organisation.id,
        "project": project.id,
    }

    # When
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["project"] == project.id
    assert response.json()["organisation"] == organisation.id


def test_create_metadata_field__project_from_different_org__returns_400(
    admin_client: APIClient,
    organisation: Organisation,
    project: Project,
) -> None:
    # Given
    other_org = Organisation.objects.create(name="Other Org")
    other_project = Project.objects.create(name="Other Project", organisation=other_org)
    url = reverse("api-v1:metadata:metadata-fields-list")
    data = {
        "name": "bad_field",
        "type": "str",
        "organisation": organisation.id,
        "project": other_project.id,
    }

    # When
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_create_metadata_field__project_admin__returns_201(
    staff_user: FFAdminUser,
    staff_client: APIClient,
    organisation: Organisation,
    project: Project,
) -> None:
    # Given
    from projects.models import UserProjectPermission

    UserProjectPermission.objects.create(user=staff_user, project=project, admin=True)

    url = reverse("api-v1:metadata:metadata-fields-list")
    data = {
        "name": "project_admin_field",
        "type": "str",
        "organisation": organisation.id,
        "project": project.id,
    }

    # When
    response = staff_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED


def test_list_metadata_fields__returns_org_level_only(
    admin_client: APIClient,
    organisation: Organisation,
    project: Project,
    project_b: Project,
) -> None:
    # Given
    org_field = MetadataField.objects.create(
        name="org_field", type="str", organisation=organisation
    )
    MetadataField.objects.create(
        name="proj_a_field", type="str", organisation=organisation, project=project
    )
    MetadataField.objects.create(
        name="proj_b_field", type="str", organisation=organisation, project=project_b
    )
    base_url = reverse("api-v1:metadata:metadata-fields-list")
    url = f"{base_url}?organisation={organisation.id}"

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    returned_ids = {r["id"] for r in response.json()["results"]}
    assert returned_ids == {org_field.id}


def test_list_metadata_fields__response_includes_nested_model_fields(
    admin_client: APIClient,
    organisation: Organisation,
    environment_content_type: ContentType,
    project_content_type: ContentType,
    project: Project,
) -> None:
    # Given
    field = MetadataField.objects.create(
        name="my_field", type="str", organisation=organisation
    )
    model_field = MetadataModelField.objects.create(
        field=field, content_type=environment_content_type
    )
    requirement = MetadataModelFieldRequirement.objects.create(
        content_type=project_content_type,
        object_id=project.id,
        model_field=model_field,
    )
    base_url = reverse("api-v1:metadata:metadata-fields-list")
    url = f"{base_url}?organisation={organisation.id}"

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["model_fields"] == [
        {
            "id": model_field.id,
            "content_type": environment_content_type.id,
            "is_required_for": [
                {
                    "content_type": project_content_type.id,
                    "object_id": project.id,
                }
            ],
        }
    ]


def test_list_project_metadata_fields__returns_project_fields_only(
    admin_client: APIClient,
    organisation: Organisation,
    project: Project,
    project_b: Project,
) -> None:
    # Given
    MetadataField.objects.create(
        name="org_field", type="str", organisation=organisation
    )
    project_field = MetadataField.objects.create(
        name="proj_a_field", type="str", organisation=organisation, project=project
    )
    MetadataField.objects.create(
        name="proj_b_field", type="str", organisation=organisation, project=project_b
    )
    url = reverse("api-v1:projects:project-metadata-fields-list", args=[project.id])

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    returned_ids = {r["id"] for r in response.json()["results"]}
    assert returned_ids == {project_field.id}


def test_list_project_metadata_fields__include_organisation__returns_both(
    admin_client: APIClient,
    organisation: Organisation,
    project: Project,
) -> None:
    # Given
    org_field = MetadataField.objects.create(
        name="org_field", type="str", organisation=organisation
    )
    project_field = MetadataField.objects.create(
        name="project_field", type="str", organisation=organisation, project=project
    )
    url = reverse("api-v1:projects:project-metadata-fields-list", args=[project.id])

    # When
    response = admin_client.get(f"{url}?include_organisation=true")

    # Then
    assert response.status_code == status.HTTP_200_OK
    returned_ids = {r["id"] for r in response.json()["results"]}
    assert org_field.id in returned_ids
    assert project_field.id in returned_ids


def test_list_project_metadata_fields__include_organisation__project_overrides_org(
    admin_client: APIClient,
    organisation: Organisation,
    project: Project,
) -> None:
    # Given
    org_field = MetadataField.objects.create(
        name="shared_name", type="str", organisation=organisation
    )
    project_field = MetadataField.objects.create(
        name="shared_name", type="int", organisation=organisation, project=project
    )
    url = reverse("api-v1:projects:project-metadata-fields-list", args=[project.id])

    # When
    response = admin_client.get(f"{url}?include_organisation=true")

    # Then
    assert response.status_code == status.HTTP_200_OK
    returned_ids = {r["id"] for r in response.json()["results"]}
    assert project_field.id in returned_ids
    assert org_field.id not in returned_ids


def test_list_project_metadata_fields__excludes_other_project_fields(
    admin_client: APIClient,
    organisation: Organisation,
    project: Project,
    project_b: Project,
) -> None:
    # Given
    project_a_field = MetadataField.objects.create(
        name="proj_a_field", type="str", organisation=organisation, project=project
    )
    MetadataField.objects.create(
        name="proj_b_field", type="str", organisation=organisation, project=project_b
    )
    url = reverse("api-v1:projects:project-metadata-fields-list", args=[project.id])

    # When
    response = admin_client.get(f"{url}?include_organisation=true")

    # Then
    assert response.status_code == status.HTTP_200_OK
    returned_ids = {r["id"] for r in response.json()["results"]}
    assert project_a_field.id in returned_ids
    assert all(
        r["project"] in (project.id, None) for r in response.json()["results"]
    )


@pytest.mark.parametrize(
    "existing_project_attr, new_project_attr, expected_status",
    [
        (None, None, status.HTTP_400_BAD_REQUEST),
        ("project", "project", status.HTTP_400_BAD_REQUEST),
        ("project", "project_b", status.HTTP_201_CREATED),
        (None, "project", status.HTTP_201_CREATED),
    ],
    ids=[
        "duplicate_org_level",
        "duplicate_project_level",
        "same_name_different_projects",
        "same_name_org_and_project_level",
    ],
)
def test_create_metadata_field__uniqueness(
    admin_client: APIClient,
    organisation: Organisation,
    project: Project,
    project_b: Project,
    existing_project_attr: str | None,
    new_project_attr: str | None,
    expected_status: int,
    request: pytest.FixtureRequest,
) -> None:
    # Given
    existing_project = (
        request.getfixturevalue(existing_project_attr)
        if existing_project_attr
        else None
    )
    MetadataField.objects.create(
        name="the_field",
        type="str",
        organisation=organisation,
        project=existing_project,
    )

    new_project = (
        request.getfixturevalue(new_project_attr) if new_project_attr else None
    )
    url = reverse("api-v1:metadata:metadata-fields-list")
    data: dict[str, object] = {
        "name": "the_field",
        "type": "str",
        "organisation": organisation.id,
    }
    if new_project is not None:
        data["project"] = new_project.id

    # When
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == expected_status
