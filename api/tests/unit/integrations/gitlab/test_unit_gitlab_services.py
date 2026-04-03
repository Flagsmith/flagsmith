import json

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from features.feature_external_resources.models import (
    FeatureExternalResource,
    ResourceType,
)
from features.models import Feature
from integrations.gitlab.constants import GitLabTag
from integrations.gitlab.models import GitLabConfiguration
from integrations.gitlab.services import get_tag_for_event, handle_gitlab_webhook_event
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
def test_get_tag_for_event__returns_correct_tag(
    event_type: str,
    action: str,
    metadata: dict[str, object],
    expected_tag: GitLabTag | None,
) -> None:
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
        **{"HTTP_X_GITLAB_TOKEN": "wrong-secret", "HTTP_X_GITLAB_EVENT": "Merge Request Hook"},  # type: ignore[arg-type]
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
        **{"HTTP_X_GITLAB_TOKEN": "some-secret", "HTTP_X_GITLAB_EVENT": "Merge Request Hook"},  # type: ignore[arg-type]
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
