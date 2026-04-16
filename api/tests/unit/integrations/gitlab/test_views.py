import pytest
from pytest_structlog import StructuredLogCapture
from rest_framework import status
from rest_framework.test import APIClient

from integrations.gitlab.models import GitLabConfiguration
from projects.models import Project


@pytest.fixture()
def gitlab_configuration(project: Project) -> GitLabConfiguration:
    return GitLabConfiguration.objects.create(  # type: ignore[no-any-return]
        project=project,
        gitlab_instance_url="https://gitlab.example.com",
        access_token="glpat-test-token",
    )


def test_create_configuration__valid_data__persists_and_masks_token(
    admin_client_new: APIClient,
    project: Project,
    log: StructuredLogCapture,
) -> None:
    # Given / When
    response = admin_client_new.post(
        f"/api/v1/projects/{project.id}/integrations/gitlab/",
        data={
            "gitlab_instance_url": "https://gitlab.example.com",
            "access_token": "glpat-xxxxxxxxxxxxxxxxxxxx",
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["access_token"] == "write-only"

    config = GitLabConfiguration.objects.get(project=project)
    assert config.gitlab_instance_url == "https://gitlab.example.com"
    assert config.access_token == "glpat-xxxxxxxxxxxxxxxxxxxx"

    assert log.events == [
        {
            "event": "gitlab-configuration-created",
            "level": "info",
            "gitlab_instance_url": "https://gitlab.example.com",
            "project__id": project.id,
            "organisation__id": project.organisation_id,
        },
    ]


def test_create_configuration__already_exists__returns_400(
    admin_client_new: APIClient,
    project: Project,
    gitlab_configuration: GitLabConfiguration,
) -> None:
    # Given / When
    response = admin_client_new.post(
        f"/api/v1/projects/{project.id}/integrations/gitlab/",
        data={
            "gitlab_instance_url": "https://gitlab.other.com",
            "access_token": "glpat-another-token",
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_update_configuration__valid_data__persists_and_masks_token(
    admin_client_new: APIClient,
    project: Project,
    gitlab_configuration: GitLabConfiguration,
    log: StructuredLogCapture,
) -> None:
    # Given / When
    response = admin_client_new.put(
        f"/api/v1/projects/{project.id}/integrations/gitlab/{gitlab_configuration.id}/",
        data={
            "gitlab_instance_url": "https://gitlab.updated.com",
            "access_token": "glpat-updated-token",
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["access_token"] == "write-only"

    gitlab_configuration.refresh_from_db()
    assert gitlab_configuration.gitlab_instance_url == "https://gitlab.updated.com"
    assert gitlab_configuration.access_token == "glpat-updated-token"

    assert log.events == [
        {
            "event": "gitlab-configuration-updated",
            "level": "info",
            "gitlab_instance_url": "https://gitlab.updated.com",
            "project__id": project.id,
            "organisation__id": project.organisation_id,
        },
    ]


def test_delete_configuration__existing__soft_deletes(
    admin_client_new: APIClient,
    project: Project,
    gitlab_configuration: GitLabConfiguration,
    log: StructuredLogCapture,
) -> None:
    # Given / When
    response = admin_client_new.delete(
        f"/api/v1/projects/{project.id}/integrations/gitlab/{gitlab_configuration.id}/",
    )

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not GitLabConfiguration.objects.filter(project=project).exists()

    assert log.events == [
        {
            "event": "gitlab-configuration-deleted",
            "level": "info",
            "project__id": project.id,
            "organisation__id": project.organisation_id,
        },
    ]


def test_list_configurations__existing__masks_token(
    admin_client_new: APIClient,
    project: Project,
    gitlab_configuration: GitLabConfiguration,
) -> None:
    # Given / When
    response = admin_client_new.get(
        f"/api/v1/projects/{project.id}/integrations/gitlab/",
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    results = response.json()
    assert len(results) == 1
    assert results[0]["gitlab_instance_url"] == "https://gitlab.example.com"
    assert results[0]["access_token"] == "write-only"


def test_create_configuration__non_admin__returns_403(
    staff_client: APIClient,
    project: Project,
) -> None:
    # Given / When
    response = staff_client.post(
        f"/api/v1/projects/{project.id}/integrations/gitlab/",
        data={
            "gitlab_instance_url": "https://gitlab.example.com",
            "access_token": "glpat-token",
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_delete_configuration__non_admin__returns_403(
    staff_client: APIClient,
    project: Project,
    gitlab_configuration: GitLabConfiguration,
) -> None:
    # Given / When
    response = staff_client.delete(
        f"/api/v1/projects/{project.id}/integrations/gitlab/{gitlab_configuration.id}/",
    )

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN
