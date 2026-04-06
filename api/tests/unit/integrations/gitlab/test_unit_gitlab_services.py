import json

import pytest
from django.urls import reverse
from pytest_mock import MockerFixture
from rest_framework import status
from rest_framework.test import APIClient

from features.feature_external_resources.models import (
    FeatureExternalResource,
    ResourceType,
)
from features.models import Feature
from integrations.gitlab.constants import GitLabEventType, GitLabTag
from integrations.gitlab.models import GitLabConfiguration
from integrations.gitlab.services import (
    dispatch_gitlab_comment,
    get_tag_for_event,
    handle_gitlab_webhook_event,
)
from projects.models import Project
from projects.tags.models import TagType


@pytest.mark.parametrize(
    "event_type,action,metadata,expected_tag",
    [
        ("merge_request", "close", {}, GitLabTag.MR_CLOSED),
        ("merge_request", "merge", {}, GitLabTag.MR_MERGED),
        ("merge_request", "open", {}, GitLabTag.MR_OPEN),
        ("merge_request", "reopen", {}, GitLabTag.MR_OPEN),
        ("merge_request", "update", {"draft": True}, GitLabTag.MR_DRAFT),
        ("merge_request", "update", {"draft": False}, None),
        ("merge_request", "update", {}, None),
        ("issue", "close", {}, GitLabTag.ISSUE_CLOSED),
        ("issue", "open", {}, GitLabTag.ISSUE_OPEN),
        ("issue", "reopen", {}, GitLabTag.ISSUE_OPEN),
        ("issue", "unknown_action", {}, None),
        ("unknown_event", "open", {}, None),
    ],
)
def test_get_tag_for_event__various_events__returns_correct_tag(
    event_type: str,
    action: str,
    metadata: dict[str, object],
    expected_tag: GitLabTag | None,
) -> None:
    # Given
    # When
    result = get_tag_for_event(event_type, action, metadata)

    # Then
    assert result == expected_tag


@pytest.mark.django_db
def test_gitlab_webhook__valid_merge_request_event__returns_200(
    project: Project,
    gitlab_configuration: GitLabConfiguration,
) -> None:
    # Given
    client = APIClient()
    url = reverse("api-v1:gitlab-webhook", args=[project.id])
    payload = json.dumps(
        {
            "object_kind": "merge_request",
            "event_type": "merge_request",
            "project": {"path_with_namespace": "testgroup/testrepo"},
            "object_attributes": {
                "action": "open",
                "url": "https://gitlab.example.com/testgroup/testrepo/-/merge_requests/1",
                "state": "opened",
                "work_in_progress": False,
            },
        }
    )

    # When
    response = client.post(
        url,
        data=payload,
        content_type="application/json",
        **{  # type: ignore[arg-type]
            "HTTP_X_GITLAB_TOKEN": gitlab_configuration.webhook_secret,
            "HTTP_X_GITLAB_EVENT": "Merge Request Hook",
        },
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["detail"] == "Event processed"


@pytest.mark.django_db
def test_gitlab_webhook__invalid_token__returns_400(
    project: Project,
    gitlab_configuration: GitLabConfiguration,
) -> None:
    # Given
    client = APIClient()
    url = reverse("api-v1:gitlab-webhook", args=[project.id])

    # When
    response = client.post(
        url,
        data="{}",
        content_type="application/json",
        **{
            "HTTP_X_GITLAB_TOKEN": "wrong-secret",
            "HTTP_X_GITLAB_EVENT": "Merge Request Hook",
        },  # type: ignore[arg-type]
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "Invalid token"


@pytest.mark.django_db
def test_gitlab_webhook__missing_config__returns_404(
    project: Project,
) -> None:
    # Given
    client = APIClient()
    url = reverse("api-v1:gitlab-webhook", args=[project.id])

    # When
    response = client.post(
        url,
        data="{}",
        content_type="application/json",
        **{
            "HTTP_X_GITLAB_TOKEN": "some-secret",
            "HTTP_X_GITLAB_EVENT": "Merge Request Hook",
        },  # type: ignore[arg-type]
    )

    # Then
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_gitlab_webhook__unhandled_event_type__returns_200_bypassed(
    project: Project,
    gitlab_configuration: GitLabConfiguration,
) -> None:
    # Given
    client = APIClient()
    url = reverse("api-v1:gitlab-webhook", args=[project.id])

    # When
    response = client.post(
        url,
        data="{}",
        content_type="application/json",
        **{  # type: ignore[arg-type]
            "HTTP_X_GITLAB_TOKEN": gitlab_configuration.webhook_secret,
            "HTTP_X_GITLAB_EVENT": "Push Hook",
        },
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["detail"] == "Event bypassed"


@pytest.mark.django_db
def test_tag_feature_per_gitlab_event__matching_feature__adds_tag(
    project: Project,
    feature: Feature,
    gitlab_configuration: GitLabConfiguration,
) -> None:
    # Given
    FeatureExternalResource.objects.create(
        url="https://gitlab.example.com/testgroup/testrepo/-/merge_requests/1",
        type=ResourceType.GITLAB_MR,
        feature=feature,
        metadata='{"state": "opened"}',
    )
    payload = {
        "object_kind": "merge_request",
        "project": {"path_with_namespace": "testgroup/testrepo"},
        "object_attributes": {
            "action": "merge",
            "url": "https://gitlab.example.com/testgroup/testrepo/-/merge_requests/1",
            "state": "merged",
            "work_in_progress": False,
        },
    }

    # When
    handle_gitlab_webhook_event(event_type="merge_request", payload=payload)

    # Then
    feature.refresh_from_db()
    gitlab_tags = feature.tags.filter(type=TagType.GITLAB.value)
    assert gitlab_tags.count() == 1
    assert gitlab_tags.first().label == GitLabTag.MR_MERGED.value  # type: ignore[union-attr]


@pytest.mark.django_db
def test_tag_feature_per_gitlab_event__tagging_disabled__does_not_add_tag(
    project: Project,
    feature: Feature,
    gitlab_configuration: GitLabConfiguration,
) -> None:
    # Given
    gitlab_configuration.tagging_enabled = False
    gitlab_configuration.save()

    FeatureExternalResource.objects.create(
        url="https://gitlab.example.com/testgroup/testrepo/-/issues/1",
        type=ResourceType.GITLAB_ISSUE,
        feature=feature,
        metadata='{"state": "opened"}',
    )
    payload = {
        "object_kind": "issue",
        "project": {"path_with_namespace": "testgroup/testrepo"},
        "object_attributes": {
            "action": "close",
            "url": "https://gitlab.example.com/testgroup/testrepo/-/issues/1",
        },
    }

    # When
    handle_gitlab_webhook_event(event_type="issue", payload=payload)

    # Then
    feature.refresh_from_db()
    assert feature.tags.filter(type=TagType.GITLAB.value).count() == 0


@pytest.mark.django_db
def test_tag_feature_per_gitlab_event__work_items_url_variant__finds_feature(
    project: Project,
    feature: Feature,
    gitlab_configuration: GitLabConfiguration,
) -> None:
    # Given — resource stored as work_items URL
    FeatureExternalResource.objects.create(
        url="https://gitlab.example.com/testgroup/testrepo/-/work_items/5",
        type=ResourceType.GITLAB_ISSUE,
        feature=feature,
        metadata='{"state": "opened"}',
    )
    # Webhook sends issues URL
    payload = {
        "object_kind": "issue",
        "project": {"path_with_namespace": "testgroup/testrepo"},
        "object_attributes": {
            "action": "close",
            "url": "https://gitlab.example.com/testgroup/testrepo/-/issues/5",
        },
    }

    # When
    handle_gitlab_webhook_event(event_type="issue", payload=payload)

    # Then
    feature.refresh_from_db()
    gitlab_tags = feature.tags.filter(type=TagType.GITLAB.value)
    assert gitlab_tags.count() == 1
    assert gitlab_tags.first().label == GitLabTag.ISSUE_CLOSED.value  # type: ignore[union-attr]


@pytest.mark.django_db
def test_dispatch_gitlab_comment__valid_feature__dispatches_task(
    project: Project,
    feature: Feature,
    gitlab_configuration: GitLabConfiguration,
    mocker: MockerFixture,
) -> None:
    # Given
    mock_task = mocker.patch("integrations.gitlab.tasks.post_gitlab_comment")

    # When
    dispatch_gitlab_comment(
        project_id=project.id,
        event_type=GitLabEventType.FLAG_UPDATED.value,
        feature=feature,
    )

    # Then
    mock_task.delay.assert_called_once()
    call_kwargs = mock_task.delay.call_args.kwargs["kwargs"]
    assert call_kwargs["project_id"] == project.id
    assert call_kwargs["feature_id"] == feature.id
    assert call_kwargs["event_type"] == GitLabEventType.FLAG_UPDATED.value


@pytest.mark.django_db
def test_dispatch_gitlab_comment__resource_removed__passes_url(
    project: Project,
    feature: Feature,
    gitlab_configuration: GitLabConfiguration,
    mocker: MockerFixture,
) -> None:
    # Given
    mock_task = mocker.patch("integrations.gitlab.tasks.post_gitlab_comment")
    resource_url = "https://gitlab.example.com/group/project/-/issues/1"

    # When
    dispatch_gitlab_comment(
        project_id=project.id,
        event_type=GitLabEventType.FEATURE_EXTERNAL_RESOURCE_REMOVED.value,
        feature=feature,
        url=resource_url,
    )

    # Then
    call_kwargs = mock_task.delay.call_args.kwargs["kwargs"]
    assert call_kwargs["url"] == resource_url


@pytest.mark.django_db
def test_dispatch_gitlab_comment__with_feature_states__maps_and_dispatches(
    project: Project,
    feature: Feature,
    environment: "Environment",
    gitlab_configuration: GitLabConfiguration,
    mocker: MockerFixture,
) -> None:
    # Given
    from features.models import FeatureState

    mock_task = mocker.patch("integrations.gitlab.tasks.post_gitlab_comment")
    feature_state = FeatureState.objects.get(
        feature=feature,
        environment=environment,
        identity__isnull=True,
        feature_segment__isnull=True,
    )

    # When
    dispatch_gitlab_comment(
        project_id=project.id,
        event_type=GitLabEventType.FLAG_UPDATED.value,
        feature=feature,
        feature_states=[feature_state],
        segment_name="beta_users",
    )

    # Then
    call_kwargs = mock_task.delay.call_args.kwargs["kwargs"]
    assert len(call_kwargs["feature_states"]) == 1
    assert call_kwargs["segment_name"] == "beta_users"
    assert call_kwargs["feature_states"][0]["environment_name"] == environment.name
