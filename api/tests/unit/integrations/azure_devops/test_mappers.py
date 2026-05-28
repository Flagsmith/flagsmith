import pytest

from features.feature_external_resources.models import (
    FeatureExternalResource,
    ResourceType,
)
from features.models import Feature
from integrations.azure_devops.constants import AzureDevOpsTagLabel
from integrations.azure_devops.mappers import (
    map_pr_state_to_tag_label,
    map_resource_to_tag_label,
    map_work_item_state_to_tag_label,
)


@pytest.mark.parametrize(
    "state, is_draft, expected",
    [
        ("active", False, AzureDevOpsTagLabel.PR_OPEN),
        ("active", True, AzureDevOpsTagLabel.PR_DRAFT),
        ("completed", False, AzureDevOpsTagLabel.PR_MERGED),
        ("completed", True, AzureDevOpsTagLabel.PR_MERGED),
        ("abandoned", False, AzureDevOpsTagLabel.PR_ABANDONED),
        ("abandoned", True, AzureDevOpsTagLabel.PR_ABANDONED),
        ("Active", False, AzureDevOpsTagLabel.PR_OPEN),
        ("Completed", False, AzureDevOpsTagLabel.PR_MERGED),
        ("ABANDONED", False, AzureDevOpsTagLabel.PR_ABANDONED),
    ],
)
def test_map_pr_state__known_state__returns_expected_label(
    state: str, is_draft: bool, expected: AzureDevOpsTagLabel
) -> None:
    # Given
    pr_state = state

    # When
    result = map_pr_state_to_tag_label(pr_state, is_draft=is_draft)

    # Then
    assert result == expected


@pytest.mark.parametrize(
    "state",
    [
        "",
        "unknown",
        "in-progress",
        "Reviewing",
    ],
)
def test_map_pr_state__unknown_state__returns_none(state: str) -> None:
    # Given
    pr_state = state

    # When
    result = map_pr_state_to_tag_label(pr_state, is_draft=False)

    # Then
    assert result is None


def test_map_pr_state__none_state__returns_none() -> None:
    # Given
    pr_state = None

    # When
    result = map_pr_state_to_tag_label(pr_state, is_draft=False)

    # Then
    assert result is None


@pytest.mark.parametrize(
    "state, expected",
    [
        ("New", AzureDevOpsTagLabel.WORK_ITEM_OPEN),
        ("Active", AzureDevOpsTagLabel.WORK_ITEM_OPEN),
        ("To Do", AzureDevOpsTagLabel.WORK_ITEM_OPEN),
        ("In Progress", AzureDevOpsTagLabel.WORK_ITEM_OPEN),
        ("Doing", AzureDevOpsTagLabel.WORK_ITEM_OPEN),
        ("Approved", AzureDevOpsTagLabel.WORK_ITEM_OPEN),
        ("Committed", AzureDevOpsTagLabel.WORK_ITEM_OPEN),
        ("Open", AzureDevOpsTagLabel.WORK_ITEM_OPEN),
        ("Proposed", AzureDevOpsTagLabel.WORK_ITEM_OPEN),
        ("Resolved", AzureDevOpsTagLabel.WORK_ITEM_OPEN),
        ("Closed", AzureDevOpsTagLabel.WORK_ITEM_CLOSED),
        ("Done", AzureDevOpsTagLabel.WORK_ITEM_CLOSED),
        ("Removed", AzureDevOpsTagLabel.WORK_ITEM_CLOSED),
        ("active", AzureDevOpsTagLabel.WORK_ITEM_OPEN),
        ("CLOSED", AzureDevOpsTagLabel.WORK_ITEM_CLOSED),
    ],
)
def test_map_work_item_state__known_state__returns_expected_label(
    state: str, expected: AzureDevOpsTagLabel
) -> None:
    # Given
    work_item_state = state

    # When
    result = map_work_item_state_to_tag_label(work_item_state)

    # Then
    assert result == expected


@pytest.mark.parametrize(
    "state",
    [
        "",
        None,
        "blocked",
        "unknown-state",
    ],
)
def test_map_work_item_state__unknown_state__returns_none(state: str | None) -> None:
    # Given
    work_item_state = state

    # When
    result = map_work_item_state_to_tag_label(work_item_state)

    # Then
    assert result is None


@pytest.mark.django_db
def test_map_resource_to_tag_label__pr_active__returns_pr_open(
    azure_devops_pr_resource_open: FeatureExternalResource,
) -> None:
    # Given
    resource = azure_devops_pr_resource_open

    # When
    label = map_resource_to_tag_label(resource)

    # Then
    assert label == AzureDevOpsTagLabel.PR_OPEN


@pytest.mark.django_db
def test_map_resource_to_tag_label__pr_draft__returns_pr_draft(
    azure_devops_pr_resource_draft: FeatureExternalResource,
) -> None:
    # Given
    resource = azure_devops_pr_resource_draft

    # When
    label = map_resource_to_tag_label(resource)

    # Then
    assert label == AzureDevOpsTagLabel.PR_DRAFT


@pytest.mark.django_db
def test_map_resource_to_tag_label__pr_completed__returns_pr_merged(
    azure_devops_pr_resource_merged: FeatureExternalResource,
) -> None:
    # Given
    resource = azure_devops_pr_resource_merged

    # When
    label = map_resource_to_tag_label(resource)

    # Then
    assert label == AzureDevOpsTagLabel.PR_MERGED


@pytest.mark.django_db
def test_map_resource_to_tag_label__work_item_active__returns_work_item_open(
    azure_devops_work_item_resource_open: FeatureExternalResource,
) -> None:
    # Given
    resource = azure_devops_work_item_resource_open

    # When
    label = map_resource_to_tag_label(resource)

    # Then
    assert label == AzureDevOpsTagLabel.WORK_ITEM_OPEN


@pytest.mark.django_db
def test_map_resource_to_tag_label__work_item_closed__returns_work_item_closed(
    azure_devops_work_item_resource_closed: FeatureExternalResource,
) -> None:
    # Given
    resource = azure_devops_work_item_resource_closed

    # When
    label = map_resource_to_tag_label(resource)

    # Then
    assert label == AzureDevOpsTagLabel.WORK_ITEM_CLOSED


@pytest.mark.django_db
def test_map_resource_to_tag_label__invalid_json_metadata__returns_none(
    feature: Feature,
) -> None:
    # Given
    resource = FeatureExternalResource.objects.create(
        feature=feature,
        url="https://dev.azure.com/test-org/proj/_git/repo/pullrequest/1",
        type=ResourceType.AZURE_DEVOPS_PULL_REQUEST.value,
        metadata="not-valid-json",
    )

    # When
    label = map_resource_to_tag_label(resource)

    # Then
    assert label is None


@pytest.mark.django_db
def test_map_resource_to_tag_label__non_ado_type__returns_none(
    feature: Feature,
) -> None:
    # Given
    resource = FeatureExternalResource.objects.create(
        feature=feature,
        url="https://gitlab.com/foo/bar/-/issues/1",
        type=ResourceType.GITLAB_ISSUE.value,
        metadata='{"state": "opened"}',
    )

    # When
    label = map_resource_to_tag_label(resource)

    # Then
    assert label is None
