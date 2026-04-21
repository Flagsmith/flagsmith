import uuid
from typing import Any, Protocol

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from features.feature_external_resources.models import ResourceType
from features.models import Feature
from integrations.gitlab.constants import GitLabTagLabel
from integrations.gitlab.models import GitLabConfiguration, GitLabWebhook
from projects.models import Project

WEBHOOK_SECRET = "valid-secret"


class LinkFeatureFixture(Protocol):
    def __call__(
        self,
        resource_url: str,
        resource_type: ResourceType,
        metadata: dict[str, Any] | None = None,
    ) -> None: ...


@pytest.fixture()
def gitlab_webhook(project: int) -> GitLabWebhook:
    project_instance = Project.objects.get(id=project)
    config = GitLabConfiguration.objects.create(
        project=project_instance,
        gitlab_instance_url="https://gitlab.example.com",
        access_token="glpat-test-token",
    )
    webhook: GitLabWebhook = GitLabWebhook.objects.create(
        gitlab_configuration=config,
        gitlab_project_id=777,
        gitlab_path_with_namespace="testorg/testrepo",
        gitlab_hook_id=42,
        secret=WEBHOOK_SECRET,
    )
    return webhook


@pytest.fixture()
def webhook_url(gitlab_webhook: GitLabWebhook) -> str:
    return reverse(
        "api-v1:gitlab-webhook",
        kwargs={"webhook_uuid": str(gitlab_webhook.uuid)},
    )


@pytest.fixture()
def link_feature(
    admin_client: APIClient,
    project: int,
    feature: int,
    gitlab_webhook: GitLabWebhook,
) -> LinkFeatureFixture:
    def _link(
        resource_url: str,
        resource_type: ResourceType,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        response = admin_client.post(
            f"/api/v1/projects/{project}/features/{feature}/feature-external-resources/",
            data={
                "type": resource_type.value,
                "url": resource_url,
                "feature": feature,
                "metadata": metadata or {},
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED, response.content

    return _link


@pytest.mark.django_db()
def test_gitlab_webhook__issue_close_event__switches_tag_to_issue_closed(
    api_client: APIClient,
    feature: int,
    webhook_url: str,
    link_feature: LinkFeatureFixture,
) -> None:
    # Given
    resource_url = "https://gitlab.example.com/testorg/testrepo/-/issues/42"
    link_feature(
        resource_url,
        ResourceType.GITLAB_ISSUE,
        metadata={"state": "opened"},
    )
    payload = {
        "object_kind": "issue",
        "object_attributes": {"url": resource_url, "state": "closed"},
    }

    # When
    response = api_client.post(
        webhook_url,
        data=payload,
        format="json",
        HTTP_X_GITLAB_TOKEN=WEBHOOK_SECRET,
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    labels = set(Feature.objects.get(id=feature).tags.values_list("label", flat=True))
    assert GitLabTagLabel.ISSUE_CLOSED.value in labels
    assert GitLabTagLabel.ISSUE_OPEN.value not in labels


@pytest.mark.django_db()
@pytest.mark.parametrize(
    "state, expected_label",
    [
        ("opened", GitLabTagLabel.ISSUE_OPEN.value),
        ("reopened", GitLabTagLabel.ISSUE_OPEN.value),
    ],
)
def test_gitlab_webhook__issue_open_events__tag_issue_open(
    api_client: APIClient,
    feature: int,
    webhook_url: str,
    link_feature: LinkFeatureFixture,
    state: str,
    expected_label: str,
) -> None:
    # Given
    resource_url = "https://gitlab.example.com/testorg/testrepo/-/issues/42"
    link_feature(resource_url, ResourceType.GITLAB_ISSUE)
    payload = {
        "object_kind": "issue",
        "object_attributes": {"url": resource_url, "state": state},
    }

    # When
    response = api_client.post(
        webhook_url,
        data=payload,
        format="json",
        HTTP_X_GITLAB_TOKEN=WEBHOOK_SECRET,
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    labels = set(Feature.objects.get(id=feature).tags.values_list("label", flat=True))
    assert expected_label in labels


@pytest.mark.django_db()
@pytest.mark.parametrize(
    "payload, expected_label",
    [
        (
            {
                "object_kind": "merge_request",
                "object_attributes": {
                    "url": "https://gitlab.example.com/testorg/testrepo/-/merge_requests/5",
                    "state": "opened",
                    "action": "open",
                    "draft": False,
                },
            },
            GitLabTagLabel.MR_OPEN.value,
        ),
        (
            {
                "object_kind": "merge_request",
                "object_attributes": {
                    "url": "https://gitlab.example.com/testorg/testrepo/-/merge_requests/5",
                    "state": "opened",
                    "action": "update",
                    "draft": True,
                },
            },
            GitLabTagLabel.MR_DRAFT.value,
        ),
        (
            {
                "object_kind": "merge_request",
                "object_attributes": {
                    "url": "https://gitlab.example.com/testorg/testrepo/-/merge_requests/5",
                    "state": "merged",
                    "action": "merge",
                    "draft": False,
                },
            },
            GitLabTagLabel.MR_MERGED.value,
        ),
        (
            {
                "object_kind": "merge_request",
                "object_attributes": {
                    "url": "https://gitlab.example.com/testorg/testrepo/-/merge_requests/5",
                    "state": "closed",
                    "action": "close",
                    "draft": False,
                },
            },
            GitLabTagLabel.MR_CLOSED.value,
        ),
    ],
)
def test_gitlab_webhook__merge_request_events__tag_reflects_state(
    api_client: APIClient,
    feature: int,
    webhook_url: str,
    link_feature: LinkFeatureFixture,
    payload: dict[str, Any],
    expected_label: str,
) -> None:
    # Given
    link_feature(payload["object_attributes"]["url"], ResourceType.GITLAB_MR)

    # When
    response = api_client.post(
        webhook_url,
        data=payload,
        format="json",
        HTTP_X_GITLAB_TOKEN=WEBHOOK_SECRET,
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    labels = set(Feature.objects.get(id=feature).tags.values_list("label", flat=True))
    assert expected_label in labels


@pytest.mark.django_db()
def test_gitlab_webhook__issue_event__does_not_touch_mr_tag_on_same_feature(
    api_client: APIClient,
    feature: int,
    webhook_url: str,
    link_feature: LinkFeatureFixture,
) -> None:
    # Given — one feature linked to both an Issue and an MR, carrying both tags.
    issue_url = "https://gitlab.example.com/testorg/testrepo/-/issues/42"
    mr_url = "https://gitlab.example.com/testorg/testrepo/-/merge_requests/7"
    link_feature(issue_url, ResourceType.GITLAB_ISSUE, metadata={"state": "opened"})
    link_feature(mr_url, ResourceType.GITLAB_MR, metadata={"state": "opened"})

    # When — the Issue is closed.
    response = api_client.post(
        webhook_url,
        data={
            "object_kind": "issue",
            "object_attributes": {"url": issue_url, "state": "closed"},
        },
        format="json",
        HTTP_X_GITLAB_TOKEN=WEBHOOK_SECRET,
    )

    # Then — Issue tag flipped to Closed, MR tag untouched.
    assert response.status_code == status.HTTP_200_OK
    labels = set(Feature.objects.get(id=feature).tags.values_list("label", flat=True))
    assert labels == {GitLabTagLabel.ISSUE_CLOSED.value, GitLabTagLabel.MR_OPEN.value}


@pytest.mark.django_db()
def test_gitlab_webhook__mr_event__does_not_touch_issue_tag_on_same_feature(
    api_client: APIClient,
    feature: int,
    webhook_url: str,
    link_feature: LinkFeatureFixture,
) -> None:
    # Given — one feature linked to both an Issue and an MR, carrying both tags.
    issue_url = "https://gitlab.example.com/testorg/testrepo/-/issues/42"
    mr_url = "https://gitlab.example.com/testorg/testrepo/-/merge_requests/7"
    link_feature(issue_url, ResourceType.GITLAB_ISSUE, metadata={"state": "opened"})
    link_feature(mr_url, ResourceType.GITLAB_MR, metadata={"state": "opened"})

    # When — the MR is merged.
    response = api_client.post(
        webhook_url,
        data={
            "object_kind": "merge_request",
            "object_attributes": {
                "url": mr_url,
                "state": "merged",
                "action": "merge",
                "draft": False,
            },
        },
        format="json",
        HTTP_X_GITLAB_TOKEN=WEBHOOK_SECRET,
    )

    # Then — MR tag flipped to Merged, Issue tag untouched.
    assert response.status_code == status.HTTP_200_OK
    labels = set(Feature.objects.get(id=feature).tags.values_list("label", flat=True))
    assert labels == {GitLabTagLabel.ISSUE_OPEN.value, GitLabTagLabel.MR_MERGED.value}


@pytest.mark.django_db()
def test_gitlab_webhook__invalid_token__returns_401_and_preserves_tags(
    api_client: APIClient,
    feature: int,
    webhook_url: str,
    link_feature: LinkFeatureFixture,
) -> None:
    # Given
    resource_url = "https://gitlab.example.com/testorg/testrepo/-/issues/42"
    link_feature(resource_url, ResourceType.GITLAB_ISSUE, metadata={"state": "opened"})

    # When
    response = api_client.post(
        webhook_url,
        data={
            "object_kind": "issue",
            "object_attributes": {"url": resource_url, "state": "closed"},
        },
        format="json",
        HTTP_X_GITLAB_TOKEN="wrong-secret",
    )

    # Then
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    labels = set(Feature.objects.get(id=feature).tags.values_list("label", flat=True))
    assert GitLabTagLabel.ISSUE_OPEN.value in labels
    assert GitLabTagLabel.ISSUE_CLOSED.value not in labels


@pytest.mark.django_db()
def test_gitlab_webhook__unknown_uuid__returns_404(
    api_client: APIClient,
) -> None:
    # Given / When
    response = api_client.post(
        reverse(
            "api-v1:gitlab-webhook",
            kwargs={"webhook_uuid": str(uuid.uuid4())},
        ),
        data={"object_kind": "issue", "object_attributes": {}},
        format="json",
        HTTP_X_GITLAB_TOKEN="whatever",
    )

    # Then
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db()
def test_gitlab_webhook__no_matching_feature__returns_200_and_no_tag_change(
    api_client: APIClient,
    feature: int,
    webhook_url: str,
) -> None:
    # Given / When
    response = api_client.post(
        webhook_url,
        data={
            "object_kind": "issue",
            "object_attributes": {
                "url": "https://gitlab.example.com/testorg/testrepo/-/issues/999",
                "state": "closed",
            },
        },
        format="json",
        HTTP_X_GITLAB_TOKEN=WEBHOOK_SECRET,
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert Feature.objects.get(id=feature).tags.count() == 0


@pytest.mark.django_db()
@pytest.mark.parametrize(
    "payload",
    [
        {"object_kind": "issue"},  # missing object_attributes
        {"object_kind": "push", "object_attributes": {"url": "x"}},  # unknown kind
        {"object_kind": "issue", "object_attributes": {"state": "opened"}},  # no url
    ],
)
def test_gitlab_webhook__payload_misses_required_field__returns_200_no_op(
    api_client: APIClient,
    feature: int,
    webhook_url: str,
    payload: dict[str, Any],
) -> None:
    # Given / When
    response = api_client.post(
        webhook_url,
        data=payload,
        format="json",
        HTTP_X_GITLAB_TOKEN=WEBHOOK_SECRET,
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert Feature.objects.get(id=feature).tags.count() == 0
