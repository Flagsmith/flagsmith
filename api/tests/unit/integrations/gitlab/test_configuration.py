import pytest
import responses
from pytest_structlog import StructuredLogCapture
from rest_framework import status
from rest_framework.test import APIClient

from features.feature_external_resources.models import (
    FeatureExternalResource,
    ResourceType,
)
from features.models import Feature
from integrations.gitlab.models import GitLabConfiguration, GitLabWebhook
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
            "event": "configuration.created",
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
            "event": "configuration.updated",
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
            "event": "configuration.deleted",
            "level": "info",
            "project__id": project.id,
            "organisation__id": project.organisation_id,
        },
    ]


@responses.activate
def test_delete_configuration__with_registered_webhooks__deregisters_each_and_clears_rows(
    admin_client_new: APIClient,
    project: Project,
    gitlab_configuration: GitLabConfiguration,
    log: StructuredLogCapture,
) -> None:
    # Given
    GitLabWebhook.objects.create(
        gitlab_configuration=gitlab_configuration,
        gitlab_project_id=100,
        gitlab_path_with_namespace="group-a/project-a",
        gitlab_hook_id=11,
        secret="secret-a",
    )
    GitLabWebhook.objects.create(
        gitlab_configuration=gitlab_configuration,
        gitlab_project_id=200,
        gitlab_path_with_namespace="group-b/project-b",
        gitlab_hook_id=22,
        secret="secret-b",
    )
    responses.delete(
        "https://gitlab.example.com/api/v4/projects/100/hooks/11",
        status=204,
    )
    responses.delete(
        "https://gitlab.example.com/api/v4/projects/200/hooks/22",
        status=204,
    )

    # When
    response = admin_client_new.delete(
        f"/api/v1/projects/{project.id}/integrations/gitlab/{gitlab_configuration.id}/",
    )

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    called = {(c.request.method, c.request.url) for c in responses.calls}
    assert (
        "DELETE",
        "https://gitlab.example.com/api/v4/projects/100/hooks/11",
    ) in called
    assert (
        "DELETE",
        "https://gitlab.example.com/api/v4/projects/200/hooks/22",
    ) in called

    deregister_events = [e for e in log.events if e["event"] == "webhook.deregistered"]
    assert len(deregister_events) == 2
    assert {e["gitlab__hook__id"] for e in deregister_events} == {11, 22}

    # Rows are cleared so a new config can register the same project afresh.
    assert not GitLabWebhook.objects.exists()


@responses.activate
def test_delete_configuration__gitlab_delete_fails_for_one__still_removes_config(
    admin_client_new: APIClient,
    project: Project,
    gitlab_configuration: GitLabConfiguration,
    log: StructuredLogCapture,
) -> None:
    # Given
    GitLabWebhook.objects.create(
        gitlab_configuration=gitlab_configuration,
        gitlab_project_id=100,
        gitlab_path_with_namespace="group-a/project-a",
        gitlab_hook_id=11,
        secret="secret-a",
    )
    GitLabWebhook.objects.create(
        gitlab_configuration=gitlab_configuration,
        gitlab_project_id=200,
        gitlab_path_with_namespace="group-b/project-b",
        gitlab_hook_id=22,
        secret="secret-b",
    )
    responses.delete(
        "https://gitlab.example.com/api/v4/projects/100/hooks/11",
        status=500,
    )
    responses.delete(
        "https://gitlab.example.com/api/v4/projects/200/hooks/22",
        status=204,
    )

    # When
    response = admin_client_new.delete(
        f"/api/v1/projects/{project.id}/integrations/gitlab/{gitlab_configuration.id}/",
    )

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not GitLabConfiguration.objects.filter(project=project).exists()
    # Second hook still deregistered; failure for the first was logged.
    assert any(
        e["event"] == "webhook.deregistered" and e["gitlab__hook__id"] == 22
        for e in log.events
    )
    assert any(
        e["event"] == "webhook.deregistration_failed" and e["gitlab__hook__id"] == 11
        for e in log.events
    )


@responses.activate
def test_delete_configuration__gitlab_hook_already_gone__treats_404_as_success(
    admin_client_new: APIClient,
    project: Project,
    gitlab_configuration: GitLabConfiguration,
    log: StructuredLogCapture,
) -> None:
    # Given
    GitLabWebhook.objects.create(
        gitlab_configuration=gitlab_configuration,
        gitlab_project_id=100,
        gitlab_path_with_namespace="group-a/project-a",
        gitlab_hook_id=11,
        secret="secret-a",
    )
    responses.delete(
        "https://gitlab.example.com/api/v4/projects/100/hooks/11",
        status=404,
    )

    # When
    response = admin_client_new.delete(
        f"/api/v1/projects/{project.id}/integrations/gitlab/{gitlab_configuration.id}/",
    )

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert any(
        e["event"] == "webhook.deregistered" and e["gitlab__hook__id"] == 11
        for e in log.events
    )


@responses.activate
def test_create_configuration__with_existing_linked_resources__backfills_webhooks(
    admin_client_new: APIClient,
    project: Project,
    log: StructuredLogCapture,
) -> None:
    # Given — two pre-existing linked resources across two distinct GitLab projects
    feature_1 = Feature.objects.create(name="Feature One", project=project)
    feature_2 = Feature.objects.create(name="Feature Two", project=project)
    FeatureExternalResource.objects.create(
        feature=feature_1,
        type=ResourceType.GITLAB_ISSUE,
        url="https://gitlab.example.com/group-a/project-a/-/issues/1",
    )
    FeatureExternalResource.objects.create(
        feature=feature_1,
        type=ResourceType.GITLAB_ISSUE,
        url="https://gitlab.example.com/group-a/project-a/-/issues/2",
    )
    FeatureExternalResource.objects.create(
        feature=feature_2,
        type=ResourceType.GITLAB_MR,
        url="https://gitlab.example.com/group-b/project-b/-/merge_requests/5",
    )
    responses.post(
        "https://gitlab.example.com/api/v4/projects/group-a%2Fproject-a/hooks",
        json={"id": 10, "project_id": 100},
        status=201,
    )
    responses.post(
        "https://gitlab.example.com/api/v4/projects/group-b%2Fproject-b/hooks",
        json={"id": 20, "project_id": 200},
        status=201,
    )

    # When
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
    config = GitLabConfiguration.objects.get(project=project)
    paths = set(
        GitLabWebhook.objects.filter(gitlab_configuration=config).values_list(
            "gitlab_path_with_namespace", flat=True
        )
    )
    assert paths == {"group-a/project-a", "group-b/project-b"}
    assert len(responses.calls) == 2


@responses.activate
def test_update_configuration__with_linked_resources_new_projects__backfills_webhooks(
    admin_client_new: APIClient,
    project: Project,
    gitlab_configuration: GitLabConfiguration,
    log: StructuredLogCapture,
) -> None:
    # Given — one project already has a webhook, another is pending
    GitLabWebhook.objects.create(
        gitlab_configuration=gitlab_configuration,
        gitlab_project_id=100,
        gitlab_path_with_namespace="group-a/project-a",
        gitlab_hook_id=10,
        secret="existing",
    )
    feature_1 = Feature.objects.create(name="Feature One", project=project)
    feature_2 = Feature.objects.create(name="Feature Two", project=project)
    FeatureExternalResource.objects.create(
        feature=feature_1,
        type=ResourceType.GITLAB_ISSUE,
        url="https://gitlab.example.com/group-a/project-a/-/issues/1",
    )
    FeatureExternalResource.objects.create(
        feature=feature_2,
        type=ResourceType.GITLAB_MR,
        url="https://gitlab.example.com/group-b/project-b/-/merge_requests/5",
    )
    responses.post(
        "https://gitlab.example.com/api/v4/projects/group-b%2Fproject-b/hooks",
        json={"id": 20, "project_id": 200},
        status=201,
    )

    # When
    response = admin_client_new.put(
        f"/api/v1/projects/{project.id}/integrations/gitlab/{gitlab_configuration.id}/",
        data={
            "gitlab_instance_url": "https://gitlab.example.com",
            "access_token": "glpat-rotated-token",
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    paths = set(
        GitLabWebhook.objects.filter(
            gitlab_configuration=gitlab_configuration
        ).values_list("gitlab_path_with_namespace", flat=True)
    )
    assert paths == {"group-a/project-a", "group-b/project-b"}
    # Only the new project was registered against GitLab (the other was already registered).
    assert len(responses.calls) == 1


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
