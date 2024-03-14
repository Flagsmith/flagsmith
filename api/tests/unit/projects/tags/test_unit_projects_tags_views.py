import json

import pytest
from django.urls import reverse
from pytest_lazyfixture import lazy_fixture
from rest_framework import status
from rest_framework.test import APIClient

from projects.models import Project
from projects.permissions import VIEW_PROJECT
from projects.tags.models import Tag
from tests.types import WithProjectPermissionsCallable


@pytest.mark.parametrize(
    "client",
    [(lazy_fixture("admin_master_api_key_client")), (lazy_fixture("admin_client"))],
)
def test_get_tag_by_uuid(client: APIClient, project: Project, tag: Tag):
    url = reverse("api-v1:projects:tags-get-by-uuid", args=[project.id, str(tag.uuid)])

    # When
    response = client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["uuid"] == str(tag.uuid)


def test_get_tag_by_uuid__returns_403_for_user_without_permission(
    staff_client: APIClient,
    organisation_one_project_two: Project,
    project: Project,
    tag: Tag,
    with_project_permissions: WithProjectPermissionsCallable,
):
    # Given
    # user with view permission for a different project
    with_project_permissions([VIEW_PROJECT], organisation_one_project_two.id)

    url = reverse(
        "api-v1:projects:tags-get-by-uuid",
        args=[project.id, str(tag.uuid)],
    )

    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_get_tag_by__uuid_returns_200_for_user_with_view_project_permission(
    staff_client: APIClient,
    project: Project,
    tag: Tag,
    with_project_permissions: WithProjectPermissionsCallable,
):
    # Given
    with_project_permissions([VIEW_PROJECT])

    url = reverse(
        "api-v1:projects:tags-get-by-uuid",
        args=[project.id, str(tag.uuid)],
    )

    # When
    response = staff_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["uuid"] == str(tag.uuid)


def test_cannot_delete_a_system_tag(
    staff_client: APIClient,
    with_project_permissions: WithProjectPermissionsCallable,
    project: Project,
    system_tag: Tag,
) -> None:
    # Given
    url = reverse("api-v1:projects:tags-detail", args=(project.id, system_tag.id))

    with_project_permissions(admin=True)

    # When
    response = staff_client.delete(url)

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"message": "Cannot delete a system tag."}


def test_cannot_update_a_system_tag(
    staff_client: APIClient,
    with_project_permissions: WithProjectPermissionsCallable,
    project: Project,
    system_tag: Tag,
):
    # Given
    url = reverse("api-v1:projects:tags-detail", args=(project.id, system_tag.id))

    with_project_permissions(admin=True)

    updated_label = f"{system_tag.label} updated"

    data = {
        "id": system_tag.id,
        "color": system_tag.color,
        "label": updated_label,
        "project": system_tag.project_id,
        "description": "",
    }

    # When
    response = staff_client.put(url, json.dumps(data), content_type="application/json")

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"non_field_errors": ["Cannot update a system tag."]}
