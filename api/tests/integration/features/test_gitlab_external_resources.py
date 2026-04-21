import json

import pytest
import responses
from pytest_structlog import StructuredLogCapture
from rest_framework import status
from rest_framework.test import APIClient

from core.helpers import get_current_site_url
from features.feature_external_resources.models import FeatureExternalResource
from features.models import Feature
from integrations.github.models import GithubConfiguration
from integrations.gitlab.models import GitLabConfiguration, GitLabWebhook
from projects.models import Project
from projects.tags.models import TagType


@pytest.mark.django_db()
def test_create_external_resource__gitlab_issue__returns_201(
    admin_client: APIClient,
    project: int,
    feature: int,
    log: StructuredLogCapture,
) -> None:
    # Given
    metadata = {"title": "Fix login bug", "state": "opened"}
    organisation_id = Project.objects.get(id=project).organisation_id

    # When
    response = admin_client.post(
        f"/api/v1/projects/{project}/features/{feature}/feature-external-resources/",
        data={
            "type": "GITLAB_ISSUE",
            "url": "https://gitlab.com/testorg/testrepo/-/work_items/42",
            "feature": feature,
            "metadata": metadata,
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    created = response.json()
    assert created["type"] == "GITLAB_ISSUE"
    assert created["url"] == "https://gitlab.com/testorg/testrepo/-/work_items/42"
    assert created["feature"] == feature
    assert created["metadata"] == metadata

    assert log.events == [
        {
            "level": "info",
            "event": "issue.linked",
            "organisation__id": organisation_id,
            "project__id": project,
            "feature__id": feature,
        },
    ]


@pytest.mark.django_db()
def test_create_external_resource__gitlab_merge_request__returns_201(
    admin_client: APIClient,
    project: int,
    feature: int,
    log: StructuredLogCapture,
) -> None:
    # Given
    metadata = {"title": "Add login button", "state": "opened"}
    organisation_id = Project.objects.get(id=project).organisation_id

    # When
    response = admin_client.post(
        f"/api/v1/projects/{project}/features/{feature}/feature-external-resources/",
        data={
            "type": "GITLAB_MR",
            "url": "https://gitlab.com/testorg/testrepo/-/merge_requests/7",
            "feature": feature,
            "metadata": metadata,
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    response_json = response.json()
    assert response_json["type"] == "GITLAB_MR"
    assert (
        response_json["url"] == "https://gitlab.com/testorg/testrepo/-/merge_requests/7"
    )
    assert response_json["metadata"] == metadata

    assert log.events == [
        {
            "level": "info",
            "event": "merge_request.linked",
            "organisation__id": organisation_id,
            "project__id": project,
            "feature__id": feature,
        },
    ]


@responses.activate
def test_create_external_resource__gitlab_issue_with_github_also_configured__returns_201(
    admin_client: APIClient,
    project: int,
    feature: int,
    log: StructuredLogCapture,
) -> None:
    # Given
    project_instance = Project.objects.get(id=project)
    organisation = project_instance.organisation

    GithubConfiguration.objects.create(
        organisation=organisation,
        installation_id="9999999",
    )
    GitLabConfiguration.objects.create(
        project=project_instance,
        gitlab_instance_url="https://gitlab.com",
        access_token="glpat-test-token",
    )
    responses.post(
        "https://gitlab.com/api/v4/projects/testorg%2Ftestrepo/hooks",
        json={"id": 1, "project_id": 1},
        status=201,
    )

    # When
    response = admin_client.post(
        f"/api/v1/projects/{project}/features/{feature}/feature-external-resources/",
        data={
            "type": "GITLAB_ISSUE",
            "url": "https://gitlab.com/testorg/testrepo/-/work_items/99",
            "feature": feature,
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["type"] == "GITLAB_ISSUE"


@responses.activate
def test_create_external_resource__gitlab_issue_with_config__registers_webhook_and_tags_feature(
    admin_client: APIClient,
    organisation: int,
    project: int,
    feature: int,
    log: StructuredLogCapture,
) -> None:
    # Given
    expected_gitlab_hook_id = 42
    expected_gitlab_project_id = 777
    project_instance = Project.objects.get(id=project)
    GitLabConfiguration.objects.create(
        project=project_instance,
        gitlab_instance_url="https://gitlab.example.com",
        access_token="glpat-test-token",
    )
    responses.post(
        "https://gitlab.example.com/api/v4/projects/testorg%2Ftestrepo/hooks",
        json={
            "id": expected_gitlab_hook_id,
            "project_id": expected_gitlab_project_id,
        },
        status=201,
    )

    # When
    response = admin_client.post(
        f"/api/v1/projects/{project}/features/{feature}/feature-external-resources/",
        data={
            "type": "GITLAB_ISSUE",
            "url": "https://gitlab.example.com/testorg/testrepo/-/issues/42",
            "feature": feature,
            "metadata": {"title": "Fix login bug", "state": "opened"},
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED

    # Webhook row persisted with GitLab's returned IDs.
    webhook = GitLabWebhook.objects.get(gitlab_configuration__project=project_instance)
    assert webhook.gitlab_hook_id == expected_gitlab_hook_id
    assert webhook.gitlab_project_id == expected_gitlab_project_id
    assert webhook.gitlab_path_with_namespace == "testorg/testrepo"

    # Registered exactly once with GitLab with the expected payload.
    [call] = responses.calls
    assert call.request.headers["PRIVATE-TOKEN"] == "glpat-test-token"
    assert json.loads(call.request.body) == {
        "url": f"{get_current_site_url()}/api/v1/gitlab-webhook/{webhook.uuid}/",
        "token": webhook.secret,
        "issues_events": True,
        "merge_requests_events": True,
        "enable_ssl_verification": True,
    }

    # Feature tagged `Issue Open`
    assert list(Feature.objects.get(id=feature).tags.values_list("label", "type")) == [
        ("Issue Open", TagType.GITLAB.value)
    ]

    # Product telemetry emitted: webhook registration + link.
    assert log.events == [
        {
            "level": "info",
            "event": "webhook.registered",
            "organisation__id": organisation,
            "project__id": project,
            "gitlab__project__id": expected_gitlab_project_id,
            "gitlab__project__path": "testorg/testrepo",
            "gitlab__hook__id": expected_gitlab_hook_id,
        },
        {
            "level": "info",
            "event": "issue.linked",
            "organisation__id": organisation,
            "project__id": project,
            "feature__id": feature,
        },
    ]


@responses.activate
def test_create_external_resource__second_link_same_gitlab_project__reuses_webhook(
    admin_client: APIClient,
    project: int,
    feature: int,
    log: StructuredLogCapture,
) -> None:
    # Given
    project_instance = Project.objects.get(id=project)
    config = GitLabConfiguration.objects.create(
        project=project_instance,
        gitlab_instance_url="https://gitlab.example.com",
        access_token="glpat-test-token",
    )
    GitLabWebhook.objects.create(
        gitlab_configuration=config,
        gitlab_project_id=777,
        gitlab_path_with_namespace="testorg/testrepo",
        gitlab_hook_id=42,
        secret="existing-secret",
    )
    # No GitLab mock is set up — if registration fires, the call will fail.

    # When
    response = admin_client.post(
        f"/api/v1/projects/{project}/features/{feature}/feature-external-resources/",
        data={
            "type": "GITLAB_MR",
            "url": "https://gitlab.example.com/testorg/testrepo/-/merge_requests/5",
            "feature": feature,
            "metadata": {"title": "Add login button", "state": "opened"},
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert len(responses.calls) == 0
    assert GitLabWebhook.objects.filter(gitlab_configuration=config).count() == 1

    # Feature tagged with `MR Open`
    assert list(Feature.objects.get(id=feature).tags.values_list("label", "type")) == [
        ("MR Open", TagType.GITLAB.value)
    ]

    # No webhook registration event
    assert "webhook.registered" not in {event["event"] for event in log.events}


@pytest.mark.django_db()
def test_create_external_resource__unparseable_url__no_webhook_registered(
    admin_client: APIClient,
    project: int,
    feature: int,
) -> None:
    # Given
    project_instance = Project.objects.get(id=project)
    GitLabConfiguration.objects.create(
        project=project_instance,
        gitlab_instance_url="https://gitlab.example.com",
        access_token="glpat-test-token",
    )

    # When — URL doesn't match our GitLab issue/MR regex.
    response = admin_client.post(
        f"/api/v1/projects/{project}/features/{feature}/feature-external-resources/",
        data={
            "type": "GITLAB_ISSUE",
            "url": "https://gitlab.example.com/not-a-resource",
            "feature": feature,
        },
        format="json",
    )

    # Then — link still succeeds, webhook registration silently skipped.
    assert response.status_code == status.HTTP_201_CREATED
    assert not GitLabWebhook.objects.exists()


@pytest.mark.django_db()
@responses.activate
def test_delete_external_resource__last_link_for_path__deregisters_webhook(
    admin_client: APIClient,
    project: int,
    feature: int,
) -> None:
    # Given — a linked resource with a registered webhook.
    project_instance = Project.objects.get(id=project)
    config = GitLabConfiguration.objects.create(
        project=project_instance,
        gitlab_instance_url="https://gitlab.example.com",
        access_token="glpat-test-token",
    )
    webhook = GitLabWebhook.objects.create(
        gitlab_configuration=config,
        gitlab_project_id=777,
        gitlab_path_with_namespace="testorg/testrepo",
        gitlab_hook_id=42,
        secret="secret",
    )
    resource = FeatureExternalResource.objects.create(
        feature=Feature.objects.get(id=feature),
        type="GITLAB_ISSUE",
        url="https://gitlab.example.com/testorg/testrepo/-/issues/1",
    )
    responses.delete(
        f"https://gitlab.example.com/api/v4/projects/{webhook.gitlab_project_id}/hooks/{webhook.gitlab_hook_id}",
        status=204,
    )

    # When
    response = admin_client.delete(
        f"/api/v1/projects/{project}/features/{feature}/feature-external-resources/{resource.id}/",
    )

    # Then — unlink succeeds and the hook is gone from GitLab and our DB.
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert len(responses.calls) == 1
    assert not GitLabWebhook.objects.filter(id=webhook.id).exists()


@pytest.mark.django_db()
@responses.activate
def test_delete_external_resource__another_link_for_path_exists__preserves_webhook(
    admin_client: APIClient,
    project: int,
    feature: int,
) -> None:
    # Given — two resources referencing the same GitLab project; one webhook.
    project_instance = Project.objects.get(id=project)
    config = GitLabConfiguration.objects.create(
        project=project_instance,
        gitlab_instance_url="https://gitlab.example.com",
        access_token="glpat-test-token",
    )
    webhook = GitLabWebhook.objects.create(
        gitlab_configuration=config,
        gitlab_project_id=777,
        gitlab_path_with_namespace="testorg/testrepo",
        gitlab_hook_id=42,
        secret="secret",
    )
    feature_obj = Feature.objects.get(id=feature)
    first = FeatureExternalResource.objects.create(
        feature=feature_obj,
        type="GITLAB_ISSUE",
        url="https://gitlab.example.com/testorg/testrepo/-/issues/1",
    )
    FeatureExternalResource.objects.create(
        feature=feature_obj,
        type="GITLAB_ISSUE",
        url="https://gitlab.example.com/testorg/testrepo/-/issues/2",
    )

    # When — unlink the first one.
    response = admin_client.delete(
        f"/api/v1/projects/{project}/features/{feature}/feature-external-resources/{first.id}/",
    )

    # Then — no GitLab DELETE fired (issue #2 still references the project),
    # webhook row untouched.
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert len(responses.calls) == 0
    assert GitLabWebhook.objects.filter(id=webhook.id).exists()


@pytest.mark.django_db()
def test_list_external_resources__gitlab_issue__returns_200(
    admin_client: APIClient,
    project: int,
    feature: int,
) -> None:
    # Given
    FeatureExternalResource.objects.create(
        url="https://gitlab.com/testorg/testrepo/-/work_items/42",
        type="GITLAB_ISSUE",
        feature=Feature.objects.get(id=feature),
        metadata='{"title": "Fix login bug", "state": "opened"}',
    )

    # When
    response = admin_client.get(
        f"/api/v1/projects/{project}/features/{feature}/feature-external-resources/",
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["type"] == "GITLAB_ISSUE"
    assert results[0]["metadata"] == {"title": "Fix login bug", "state": "opened"}


@pytest.mark.django_db()
def test_list_external_resources__gitlab_merge_request__returns_200(
    admin_client: APIClient,
    project: int,
    feature: int,
) -> None:
    # Given
    FeatureExternalResource.objects.create(
        url="https://gitlab.com/testorg/testrepo/-/merge_requests/7",
        type="GITLAB_MR",
        feature=Feature.objects.get(id=feature),
        metadata='{"title": "Add login button", "state": "opened"}',
    )

    # When
    response = admin_client.get(
        f"/api/v1/projects/{project}/features/{feature}/feature-external-resources/",
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    results = response.json()["results"]
    assert len(results) == 1
    assert results[0]["type"] == "GITLAB_MR"
    assert results[0]["metadata"] == {"title": "Add login button", "state": "opened"}
