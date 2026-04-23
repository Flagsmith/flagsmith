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


<<<<<<< HEAD
=======

@pytest.fixture()
def gitlab_config(project: int) -> GitLabConfiguration:
    config: GitLabConfiguration = GitLabConfiguration.objects.create(
        project=Project.objects.get(id=project),
        gitlab_instance_url=GITLAB_INSTANCE_URL,
        access_token=GITLAB_ACCESS_TOKEN,
    )
    return config


@pytest.fixture()
def gitlab_config_with_labeling(project: int) -> GitLabConfiguration:
    config: GitLabConfiguration = GitLabConfiguration.objects.create(
        project=Project.objects.get(id=project),
        gitlab_instance_url=GITLAB_INSTANCE_URL,
        access_token=GITLAB_ACCESS_TOKEN,
        labeling_enabled=True,
    )
    return config


def _mock_webhook_registration() -> None:
    responses.post(GITLAB_HOOKS_URL, json={"id": 1, "project_id": 1}, status=201)


@pytest.mark.django_db()
>>>>>>> ee9265c90 (feat: rename tagging_enabled to labeling_enabled on GitLabConfiguration)
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
            "event": "resource.linked",
            "organisation__id": organisation,
            "project__id": project,
            "feature__id": feature,
            "resource__type": "gitlab_issue",
        },
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
            "event": "resource.linked",
            "organisation__id": organisation,
            "project__id": project,
            "feature__id": feature,
            "resource__type": "gitlab_mr",
        },
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
            "event": "resource.linked",
            "organisation__id": organisation,
            "project__id": project,
            "feature__id": feature,
            "resource__type": "gitlab_mr",
        },
        {
            "level": "info",
            "event": "comment.posted",
            "organisation__id": organisation,
            "project__id": project,
            "feature__id": feature,
            "gitlab__project__path": "testorg/testrepo",
            "gitlab__resource__iid": 5,
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
<<<<<<< HEAD
=======


@pytest.mark.django_db()
@responses.activate
def test_create_external_resource__gitlab_issue_with_labeling_enabled__creates_and_applies_label(
    admin_client: APIClient,
    project: int,
    feature: int,
    gitlab_config_with_labeling: GitLabConfiguration,
    log: StructuredLogCapture,
) -> None:
    # Given
    label_create = responses.post(
        GITLAB_LABELS_URL,
        json={"id": 1, "name": "Flagsmith Feature"},
        status=201,
        match=[
            responses.matchers.header_matcher({"PRIVATE-TOKEN": GITLAB_ACCESS_TOKEN}),
            responses.matchers.json_params_matcher(
                {
                    "name": "Flagsmith Feature",
                    "color": "#6633FF",
                    "description": (
                        "This GitLab Issue/MR is linked to a Flagsmith Feature Flag"
                    ),
                },
            ),
        ],
    )
    label_apply = responses.put(
        GITLAB_ISSUE_API_URL,
        json={"iid": 42, "labels": ["Flagsmith Feature"]},
        status=200,
        match=[
            responses.matchers.json_params_matcher({"add_labels": "Flagsmith Feature"}),
        ],
    )
    _mock_webhook_registration()

    # When
    response = admin_client.post(
        f"/api/v1/projects/{project}/features/{feature}/feature-external-resources/",
        data={"type": "GITLAB_ISSUE", "url": GITLAB_ISSUE_URL, "feature": feature},
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert label_create.call_count == 1
    assert label_apply.call_count == 1
    assert FeatureExternalResource.objects.count() == 1
    assert [e["event"] for e in log.events] == [
        "label.created",
        "webhook.registered",
        "issue.linked",
    ]


@pytest.mark.django_db()
@responses.activate
def test_create_external_resource__gitlab_mr_with_labeling_enabled__creates_and_applies_label(
    admin_client: APIClient,
    project: int,
    feature: int,
    gitlab_config_with_labeling: GitLabConfiguration,
    log: StructuredLogCapture,
) -> None:
    # Given
    responses.post(
        GITLAB_LABELS_URL,
        json={"id": 1, "name": "Flagsmith Feature"},
        status=201,
    )
    label_apply = responses.put(
        GITLAB_MR_API_URL,
        json={"iid": 7, "labels": ["Flagsmith Feature"]},
        status=200,
        match=[
            responses.matchers.json_params_matcher({"add_labels": "Flagsmith Feature"}),
        ],
    )
    _mock_webhook_registration()

    # When
    response = admin_client.post(
        f"/api/v1/projects/{project}/features/{feature}/feature-external-resources/",
        data={"type": "GITLAB_MR", "url": GITLAB_MR_URL, "feature": feature},
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert label_apply.call_count == 1
    assert [e["event"] for e in log.events] == [
        "label.created",
        "webhook.registered",
        "merge_request.linked",
    ]


@pytest.mark.django_db()
@responses.activate
def test_create_external_resource__gitlab_issue_with_labeling_disabled__skips_label_api(
    admin_client: APIClient,
    project: int,
    feature: int,
    gitlab_config: GitLabConfiguration,
    log: StructuredLogCapture,
) -> None:
    # Given
    _mock_webhook_registration()

    # When
    response = admin_client.post(
        f"/api/v1/projects/{project}/features/{feature}/feature-external-resources/",
        data={"type": "GITLAB_ISSUE", "url": GITLAB_ISSUE_URL, "feature": feature},
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert [e["event"] for e in log.events] == ["webhook.registered", "issue.linked"]


@pytest.mark.django_db()
@responses.activate
def test_create_external_resource__gitlab_issue_label_already_exists__applies_label(
    admin_client: APIClient,
    project: int,
    feature: int,
    gitlab_config_with_labeling: GitLabConfiguration,
    log: StructuredLogCapture,
) -> None:
    # Given
    responses.post(
        GITLAB_LABELS_URL,
        json={"message": {"title": ["has already been taken"]}},
        status=409,
    )
    label_apply = responses.put(
        GITLAB_ISSUE_API_URL,
        json={"iid": 42, "labels": ["Flagsmith Feature"]},
        status=200,
    )
    _mock_webhook_registration()

    # When
    response = admin_client.post(
        f"/api/v1/projects/{project}/features/{feature}/feature-external-resources/",
        data={"type": "GITLAB_ISSUE", "url": GITLAB_ISSUE_URL, "feature": feature},
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert label_apply.call_count == 1
    assert [e["event"] for e in log.events] == [
        "webhook.registered",
        "issue.linked",
    ]


@pytest.mark.django_db()
@responses.activate
def test_create_external_resource__gitlab_issue_label_apply_fails__rolls_back_link(
    admin_client: APIClient,
    project: int,
    feature: int,
    gitlab_config_with_labeling: GitLabConfiguration,
    log: StructuredLogCapture,
) -> None:
    # Given
    responses.post(
        GITLAB_LABELS_URL,
        json={"id": 1, "name": "Flagsmith Feature"},
        status=201,
    )
    responses.put(GITLAB_ISSUE_API_URL, json={"message": "403 Forbidden"}, status=403)

    # When
    response = admin_client.post(
        f"/api/v1/projects/{project}/features/{feature}/feature-external-resources/",
        data={"type": "GITLAB_ISSUE", "url": GITLAB_ISSUE_URL, "feature": feature},
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert FeatureExternalResource.objects.count() == 0
    assert [e["event"] for e in log.events] == ["label.created", "label.failed"]


@pytest.mark.django_db()
@responses.activate
def test_create_external_resource__gitlab_issue_label_create_fails__rolls_back_link(
    admin_client: APIClient,
    project: int,
    feature: int,
    gitlab_config_with_labeling: GitLabConfiguration,
    log: StructuredLogCapture,
) -> None:
    # Given
    responses.post(
        GITLAB_LABELS_URL,
        json={"message": "internal server error"},
        status=500,
    )

    # When
    response = admin_client.post(
        f"/api/v1/projects/{project}/features/{feature}/feature-external-resources/",
        data={"type": "GITLAB_ISSUE", "url": GITLAB_ISSUE_URL, "feature": feature},
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert FeatureExternalResource.objects.count() == 0
    assert [e["event"] for e in log.events] == ["label.failed"]


@pytest.mark.django_db()
@responses.activate
def test_create_external_resource__gitlab_issue_invalid_url__rolls_back_link(
    admin_client: APIClient,
    project: int,
    feature: int,
    gitlab_config_with_labeling: GitLabConfiguration,
) -> None:
    # Given / When
    response = admin_client.post(
        f"/api/v1/projects/{project}/features/{feature}/feature-external-resources/",
        data={
            "type": "GITLAB_ISSUE",
            "url": f"{GITLAB_INSTANCE_URL}/not-a-valid-resource-url",
            "feature": feature,
        },
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"url": "Could not parse GitLab resource URL."}
    assert FeatureExternalResource.objects.count() == 0


@pytest.mark.django_db()
@responses.activate
@pytest.mark.parametrize(
    "other_links_count, expected_removal_calls",
    [(0, 1), (1, 0)],
    ids=["last_link_removes_label", "shared_link_keeps_label"],
)
def test_delete_external_resource__gitlab_issue__removes_label_only_when_last_link(
    other_links_count: int,
    expected_removal_calls: int,
    admin_client: APIClient,
    project: int,
    feature: int,
    gitlab_config_with_labeling: GitLabConfiguration,
) -> None:
    # Given
    resource = FeatureExternalResource.objects.create(
        url=GITLAB_ISSUE_URL,
        type="GITLAB_ISSUE",
        feature=Feature.objects.get(id=feature),
    )
    for i in range(other_links_count):
        other_feature = Feature.objects.create(
            name=f"other_feature_{i}",
            project=gitlab_config_with_labeling.project,
        )
        FeatureExternalResource.objects.create(
            url=GITLAB_ISSUE_URL,
            type="GITLAB_ISSUE",
            feature=other_feature,
        )
    label_remove = responses.put(
        GITLAB_ISSUE_API_URL,
        json={"iid": 42, "labels": []},
        status=200,
        match=[
            responses.matchers.json_params_matcher({"remove_labels": "Flagsmith Feature"}),
        ],
    )

    # When
    response = admin_client.delete(
        f"/api/v1/projects/{project}/features/{feature}"
        f"/feature-external-resources/{resource.id}/",
    )

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert label_remove.call_count == expected_removal_calls


@pytest.mark.django_db()
@responses.activate
def test_delete_external_resource__gitlab_mr_last_link__removes_label(
    admin_client: APIClient,
    project: int,
    feature: int,
    gitlab_config_with_labeling: GitLabConfiguration,
) -> None:
    # Given
    resource = FeatureExternalResource.objects.create(
        url=GITLAB_MR_URL,
        type="GITLAB_MR",
        feature=Feature.objects.get(id=feature),
    )
    label_remove = responses.put(
        GITLAB_MR_API_URL,
        json={"iid": 7, "labels": []},
        status=200,
        match=[
            responses.matchers.json_params_matcher({"remove_labels": "Flagsmith Feature"}),
        ],
    )

    # When
    response = admin_client.delete(
        f"/api/v1/projects/{project}/features/{feature}"
        f"/feature-external-resources/{resource.id}/",
    )

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert label_remove.call_count == 1


@pytest.mark.django_db()
@responses.activate
def test_delete_external_resource__gitlab_label_removal_fails__unlink_still_succeeds(
    admin_client: APIClient,
    project: int,
    feature: int,
    gitlab_config_with_labeling: GitLabConfiguration,
    log: StructuredLogCapture,
) -> None:
    # Given
    resource = FeatureExternalResource.objects.create(
        url=GITLAB_ISSUE_URL,
        type="GITLAB_ISSUE",
        feature=Feature.objects.get(id=feature),
    )
    responses.put(
        GITLAB_ISSUE_API_URL,
        json={"message": "500 Internal Server Error"},
        status=500,
    )

    # When
    response = admin_client.delete(
        f"/api/v1/projects/{project}/features/{feature}"
        f"/feature-external-resources/{resource.id}/",
    )

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not FeatureExternalResource.objects.filter(pk=resource.pk).exists()
    assert "label.removal_failed" in {e["event"] for e in log.events}
>>>>>>> ee9265c90 (feat: rename tagging_enabled to labeling_enabled on GitLabConfiguration)
