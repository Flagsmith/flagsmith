import json

import pytest

from features.feature_external_resources.models import (
    FeatureExternalResource,
    ResourceType,
)
from features.models import Feature
from integrations.gitlab.models import GitLabWebhook
from integrations.gitlab.services.metadata import update_resource_metadata


@pytest.mark.django_db
def test_update_resource_metadata__issue_state_changed__updates_metadata(
    feature: Feature,
    gitlab_webhook: GitLabWebhook,
) -> None:
    # Given
    resource = FeatureExternalResource.objects.create(
        feature=feature,
        url="https://gitlab.example.com/testorg/testrepo/-/issues/1",
        type=ResourceType.GITLAB_ISSUE.value,
        metadata='{"state": "opened", "title": "Bug"}',
    )

    # When
    update_resource_metadata(
        webhook=gitlab_webhook,
        payload={
            "object_kind": "issue",
            "object_attributes": {
                "url": "https://gitlab.example.com/testorg/testrepo/-/issues/1",
                "state": "closed",
                "action": "close",
                "title": "Bug",
            },
        },
    )

    # Then
    resource.refresh_from_db()
    assert resource.metadata is not None
    assert json.loads(resource.metadata) == {"state": "closed", "title": "Bug"}


@pytest.mark.django_db
def test_update_resource_metadata__issue_title_changed__updates_metadata(
    feature: Feature,
    gitlab_webhook: GitLabWebhook,
) -> None:
    # Given
    resource = FeatureExternalResource.objects.create(
        feature=feature,
        url="https://gitlab.example.com/testorg/testrepo/-/issues/1",
        type=ResourceType.GITLAB_ISSUE.value,
        metadata='{"state": "opened", "title": "Old name"}',
    )

    # When
    update_resource_metadata(
        webhook=gitlab_webhook,
        payload={
            "object_kind": "issue",
            "object_attributes": {
                "url": "https://gitlab.example.com/testorg/testrepo/-/issues/1",
                "state": "opened",
                "title": "New name",
            },
        },
    )

    # Then
    resource.refresh_from_db()
    assert resource.metadata is not None
    assert json.loads(resource.metadata) == {"state": "opened", "title": "New name"}


@pytest.mark.django_db
def test_update_resource_metadata__work_item_url_matches_legacy_issue__updates(
    feature: Feature,
    gitlab_webhook: GitLabWebhook,
) -> None:
    # Given
    resource = FeatureExternalResource.objects.create(
        feature=feature,
        url="https://gitlab.example.com/testorg/testrepo/-/issues/1",
        type=ResourceType.GITLAB_ISSUE.value,
        metadata='{"state": "opened"}',
    )

    # When
    update_resource_metadata(
        webhook=gitlab_webhook,
        payload={
            "object_kind": "issue",
            "object_attributes": {
                "url": "https://gitlab.example.com/testorg/testrepo/-/work_items/1",
                "state": "closed",
            },
        },
    )

    # Then
    resource.refresh_from_db()
    assert resource.metadata is not None
    assert json.loads(resource.metadata) == {"state": "closed"}


@pytest.mark.django_db
def test_update_resource_metadata__merge_request_action_merge__sets_merged_state(
    feature: Feature,
    gitlab_webhook: GitLabWebhook,
) -> None:
    # Given
    resource = FeatureExternalResource.objects.create(
        feature=feature,
        url="https://gitlab.example.com/testorg/testrepo/-/merge_requests/7",
        type=ResourceType.GITLAB_MR.value,
        metadata='{"state": "opened", "title": "MR", "draft": false}',
    )

    # When
    update_resource_metadata(
        webhook=gitlab_webhook,
        payload={
            "object_kind": "merge_request",
            "object_attributes": {
                "url": "https://gitlab.example.com/testorg/testrepo/-/merge_requests/7",
                "state": "opened",
                "action": "merge",
                "draft": False,
            },
        },
    )

    # Then
    resource.refresh_from_db()
    assert resource.metadata is not None
    assert json.loads(resource.metadata) == {
        "state": "merged",
        "title": "MR",
        "draft": False,
    }


@pytest.mark.django_db
def test_update_resource_metadata__merge_request_draft_toggled__updates_draft(
    feature: Feature,
    gitlab_webhook: GitLabWebhook,
) -> None:
    # Given
    resource = FeatureExternalResource.objects.create(
        feature=feature,
        url="https://gitlab.example.com/testorg/testrepo/-/merge_requests/7",
        type=ResourceType.GITLAB_MR.value,
        metadata='{"state": "opened", "draft": true}',
    )

    # When
    update_resource_metadata(
        webhook=gitlab_webhook,
        payload={
            "object_kind": "merge_request",
            "object_attributes": {
                "url": "https://gitlab.example.com/testorg/testrepo/-/merge_requests/7",
                "state": "opened",
                "draft": False,
            },
        },
    )

    # Then
    resource.refresh_from_db()
    assert resource.metadata is not None
    assert json.loads(resource.metadata) == {"state": "opened", "draft": False}


@pytest.mark.django_db
def test_update_resource_metadata__merge_request_work_in_progress_only__updates_draft(
    feature: Feature,
    gitlab_webhook: GitLabWebhook,
) -> None:
    # Given
    resource = FeatureExternalResource.objects.create(
        feature=feature,
        url="https://gitlab.example.com/testorg/testrepo/-/merge_requests/7",
        type=ResourceType.GITLAB_MR.value,
        metadata='{"state": "opened", "draft": false}',
    )

    # When
    update_resource_metadata(
        webhook=gitlab_webhook,
        payload={
            "object_kind": "merge_request",
            "object_attributes": {
                "url": "https://gitlab.example.com/testorg/testrepo/-/merge_requests/7",
                "state": "opened",
                "work_in_progress": True,
            },
        },
    )

    # Then
    resource.refresh_from_db()
    assert resource.metadata is not None
    assert json.loads(resource.metadata) == {"state": "opened", "draft": True}


@pytest.mark.django_db
def test_update_resource_metadata__nothing_changed__skips_write(
    feature: Feature,
    gitlab_webhook: GitLabWebhook,
) -> None:
    # Given
    resource = FeatureExternalResource.objects.create(
        feature=feature,
        url="https://gitlab.example.com/testorg/testrepo/-/issues/1",
        type=ResourceType.GITLAB_ISSUE.value,
        metadata='{"state": "opened"}',
    )

    # When
    update_resource_metadata(
        webhook=gitlab_webhook,
        payload={
            "object_kind": "issue",
            "object_attributes": {
                "url": "https://gitlab.example.com/testorg/testrepo/-/issues/1",
                "state": "opened",
            },
        },
    )

    # Then
    resource.refresh_from_db()
    assert resource.metadata is not None
    assert json.loads(resource.metadata) == {"state": "opened"}


@pytest.mark.django_db
def test_update_resource_metadata__no_linked_resource__noop(
    gitlab_webhook: GitLabWebhook,
) -> None:
    # Given / When
    update_resource_metadata(
        webhook=gitlab_webhook,
        payload={
            "object_kind": "issue",
            "object_attributes": {
                "url": "https://gitlab.example.com/testorg/testrepo/-/issues/999",
                "state": "closed",
            },
        },
    )

    # Then — no exception raised
    assert not FeatureExternalResource.objects.exists()


@pytest.mark.django_db
def test_update_resource_metadata__unsupported_object_kind__noop(
    feature: Feature,
    gitlab_webhook: GitLabWebhook,
) -> None:
    # Given
    resource = FeatureExternalResource.objects.create(
        feature=feature,
        url="https://gitlab.example.com/testorg/testrepo/-/issues/1",
        type=ResourceType.GITLAB_ISSUE.value,
        metadata='{"state": "opened"}',
    )

    # When
    update_resource_metadata(
        webhook=gitlab_webhook,
        payload={
            "object_kind": "push",
            "object_attributes": {
                "url": "https://gitlab.example.com/testorg/testrepo/-/issues/1",
                "state": "closed",
            },
        },
    )

    # Then
    resource.refresh_from_db()
    assert resource.metadata is not None
    assert json.loads(resource.metadata) == {"state": "opened"}
