import json

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
            "event": "resource.linked",
            "organisation__id": organisation_id,
            "project__id": project,
            "feature__id": feature,
            "resource__type": "gitlab_issue",
        },
    ]


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
            "event": "resource.linked",
            "organisation__id": organisation_id,
            "project__id": project,
            "feature__id": feature,
            "resource__type": "gitlab_mr",
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
    responses.post(
        "https://gitlab.com/api/v4/projects/testorg%2Ftestrepo/issues/99/notes",
        json={"id": 1},
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
def test_create_external_resource__gitlab_issue__registers_webhook_and_tags_feature(
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
    responses.post(
        "https://gitlab.example.com/api/v4/projects/testorg%2Ftestrepo/issues/42/notes",
        json={"id": 1},
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
    hook_call, *_ = responses.calls
    assert hook_call.request.headers["PRIVATE-TOKEN"] == "glpat-test-token"
    assert json.loads(hook_call.request.body) == {
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
            "event": "comment.posted",
            "organisation__id": organisation,
            "project__id": project,
            "feature__id": feature,
            "gitlab__project__path": "testorg/testrepo",
            "gitlab__resource__iid": 42,
        },
        {
            "level": "info",
            "event": "resource.linked",
            "organisation__id": organisation,
            "project__id": project,
            "feature__id": feature,
            "resource__type": "gitlab_issue",
        },
    ]


@responses.activate
def test_create_external_resource__gitlab_mr__registers_webhook_and_tags_feature(
    admin_client: APIClient,
    organisation: int,
    project: int,
    feature: int,
    log: StructuredLogCapture,
) -> None:
    # Given
    project_instance = Project.objects.get(id=project)
    GitLabConfiguration.objects.create(
        project=project_instance,
        gitlab_instance_url="https://gitlab.example.com",
        access_token="glpat-test-token",
    )
    responses.post(
        "https://gitlab.example.com/api/v4/projects/testorg%2Ftestrepo/hooks",
        json={"id": 77, "project_id": 777},
        status=201,
    )
    responses.post(
        "https://gitlab.example.com/api/v4/projects/testorg%2Ftestrepo/merge_requests/7/notes",
        json={"id": 1},
        status=201,
    )

    # When
    response = admin_client.post(
        f"/api/v1/projects/{project}/features/{feature}/feature-external-resources/",
        data={
            "type": "GITLAB_MR",
            "url": "https://gitlab.example.com/testorg/testrepo/-/merge_requests/7",
            "feature": feature,
            "metadata": {
                "title": "Add login button",
                "state": "opened",
                "draft": False,
            },
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert GitLabWebhook.objects.filter(
        gitlab_configuration__project=project_instance,
        gitlab_path_with_namespace="testorg/testrepo",
    ).exists()
    assert list(Feature.objects.get(id=feature).tags.values_list("label", "type")) == [
        ("MR Open", TagType.GITLAB.value)
    ]
    assert log.events == [
        {
            "level": "info",
            "event": "webhook.registered",
            "organisation__id": organisation,
            "project__id": project,
            "gitlab__project__id": 777,
            "gitlab__project__path": "testorg/testrepo",
            "gitlab__hook__id": 77,
        },
        {
            "level": "info",
            "event": "comment.posted",
            "organisation__id": organisation,
            "project__id": project,
            "feature__id": feature,
            "gitlab__project__path": "testorg/testrepo",
            "gitlab__resource__iid": 7,
        },
        {
            "level": "info",
            "event": "resource.linked",
            "organisation__id": organisation,
            "project__id": project,
            "feature__id": feature,
            "resource__type": "gitlab_mr",
        },
    ]


@responses.activate
def test_create_external_resource__second_link_same_gitlab_project__reuses_webhook(
    admin_client: APIClient,
    organisation: int,
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
    responses.post(
        "https://gitlab.example.com/api/v4/projects/testorg%2Ftestrepo/merge_requests/5/notes",
        json={"id": 1},
        status=201,
    )

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
    assert GitLabWebhook.objects.filter(gitlab_configuration=config).count() == 1

    # Feature tagged with `MR Open`
    assert list(Feature.objects.get(id=feature).tags.values_list("label", "type")) == [
        ("MR Open", TagType.GITLAB.value)
    ]

    assert log.events == [
        {
            "level": "info",
            "event": "comment.posted",
            "organisation__id": organisation,
            "project__id": project,
            "feature__id": feature,
            "gitlab__project__path": "testorg/testrepo",
            "gitlab__resource__iid": 5,
        },
        {
            "level": "info",
            "event": "resource.linked",
            "organisation__id": organisation,
            "project__id": project,
            "feature__id": feature,
            "resource__type": "gitlab_mr",
        },
    ]


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

    # When
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


@responses.activate
def test_delete_external_resource__last_link_for_path__deregisters_webhook_and_posts_comment(
    admin_client: APIClient,
    organisation: int,
    project: int,
    feature: int,
    feature_name: str,
    log: StructuredLogCapture,
) -> None:
    # Given
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
    responses.post(
        "https://gitlab.example.com/api/v4/projects/testorg%2Ftestrepo/issues/1/notes",
        json={"id": 1},
        status=201,
    )

    # When
    response = admin_client.delete(
        f"/api/v1/projects/{project}/features/{feature}/feature-external-resources/{resource.id}/",
    )

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not GitLabWebhook.objects.filter(id=webhook.id).exists()

    [note_call] = [c for c in responses.calls if "/notes" in c.request.url]
    assert json.loads(note_call.request.body)["body"] == (
        f"⛓️‍💥 Unlinked from Flagsmith feature flag `{feature_name}`\n"
    )

    assert log.events == [
        {
            "level": "info",
            "event": "comment.posted",
            "organisation__id": organisation,
            "project__id": project,
            "feature__id": feature,
            "gitlab__project__path": "testorg/testrepo",
            "gitlab__resource__iid": 1,
        },
        {
            "level": "info",
            "event": "webhook.deregistered",
            "organisation__id": organisation,
            "project__id": project,
            "gitlab__project__id": 777,
            "gitlab__hook__id": 42,
        },
        {
            "level": "info",
            "event": "resource.unlinked",
            "organisation__id": organisation,
            "project__id": project,
            "feature__id": feature,
            "resource__type": "gitlab_issue",
        },
    ]


@responses.activate
def test_delete_external_resource__another_link_for_path_exists__preserves_webhook(
    admin_client: APIClient,
    project: int,
    feature: int,
) -> None:
    # Given
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
    responses.post(
        "https://gitlab.example.com/api/v4/projects/testorg%2Ftestrepo/issues/1/notes",
        json={"id": 1},
        status=201,
    )

    # When
    response = admin_client.delete(
        f"/api/v1/projects/{project}/features/{feature}/feature-external-resources/{first.id}/",
    )

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    [call] = responses.calls
    assert "/notes" in call.request.url
    assert GitLabWebhook.objects.filter(id=webhook.id).exists()


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


@responses.activate
def test_create_external_resource__gitlab_issue_with_labeling__applies_label(
    admin_client: APIClient,
    organisation: int,
    project: int,
    feature: int,
    log: StructuredLogCapture,
) -> None:
    # Given
    project_instance = Project.objects.get(id=project)
    GitLabConfiguration.objects.create(
        project=project_instance,
        gitlab_instance_url="https://gitlab.example.com",
        access_token="glpat-test-token",
        labeling_enabled=True,
    )
    responses.post(
        "https://gitlab.example.com/api/v4/projects/testorg%2Ftestrepo/labels",
        json={"name": "Flagsmith Feature"},
        status=201,
    )
    responses.put(
        "https://gitlab.example.com/api/v4/projects/testorg%2Ftestrepo/issues/42",
        json={"iid": 42},
        status=200,
        match=[
            responses.matchers.json_params_matcher(
                {"add_labels": "Flagsmith Feature"},
            ),
        ],
    )
    responses.post(
        "https://gitlab.example.com/api/v4/projects/testorg%2Ftestrepo/hooks",
        json={"id": 1, "project_id": 1},
        status=201,
    )
    responses.post(
        "https://gitlab.example.com/api/v4/projects/testorg%2Ftestrepo/issues/42/notes",
        json={"id": 1},
        status=201,
    )

    # When
    response = admin_client.post(
        f"/api/v1/projects/{project}/features/{feature}/feature-external-resources/",
        data={
            "type": "GITLAB_ISSUE",
            "url": "https://gitlab.example.com/testorg/testrepo/-/issues/42",
            "feature": feature,
            "metadata": {"title": "Bug fix", "state": "opened"},
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert any(e["event"] == "label.created" for e in log.events)
    assert any(e["event"] == "resource.linked" for e in log.events)


@responses.activate
def test_create_external_resource__gitlab_issue_with_labeling_disabled__skips_label_api(
    admin_client: APIClient,
    project: int,
    feature: int,
    log: StructuredLogCapture,
) -> None:
    # Given
    project_instance = Project.objects.get(id=project)
    GitLabConfiguration.objects.create(
        project=project_instance,
        gitlab_instance_url="https://gitlab.example.com",
        access_token="glpat-test-token",
        labeling_enabled=False,
    )
    responses.post(
        "https://gitlab.example.com/api/v4/projects/testorg%2Ftestrepo/hooks",
        json={"id": 1, "project_id": 1},
        status=201,
    )
    responses.post(
        "https://gitlab.example.com/api/v4/projects/testorg%2Ftestrepo/issues/42/notes",
        json={"id": 1},
        status=201,
    )

    # When
    response = admin_client.post(
        f"/api/v1/projects/{project}/features/{feature}/feature-external-resources/",
        data={
            "type": "GITLAB_ISSUE",
            "url": "https://gitlab.example.com/testorg/testrepo/-/issues/42",
            "feature": feature,
            "metadata": {"title": "Bug fix", "state": "opened"},
        },
        format="json",
    )

    # Then — no label API called, resource still created.
    assert response.status_code == status.HTTP_201_CREATED
    assert not any(e["event"] == "label.created" for e in log.events)


@responses.activate
def test_create_external_resource__gitlab_issue_label_api_failure__returns_400(
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
        labeling_enabled=True,
    )
    responses.post(
        "https://gitlab.example.com/api/v4/projects/testorg%2Ftestrepo/labels",
        status=403,
    )

    # When
    response = admin_client.post(
        f"/api/v1/projects/{project}/features/{feature}/feature-external-resources/",
        data={
            "type": "GITLAB_ISSUE",
            "url": "https://gitlab.example.com/testorg/testrepo/-/issues/42",
            "feature": feature,
            "metadata": {"title": "Bug fix", "state": "opened"},
        },
        format="json",
    )

    # Then — resource not created, transaction rolled back.
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert not FeatureExternalResource.objects.exists()


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
