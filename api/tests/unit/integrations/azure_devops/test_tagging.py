import pytest

from features.feature_external_resources.models import (
    FeatureExternalResource,
    ResourceType,
)
from features.models import Feature
from integrations.azure_devops.models import AzureDevOpsConfiguration
from integrations.azure_devops.services.tagging import (
    apply_initial_tag,
    clear_tag_for_resource,
    refresh_tags_for_resource,
)
from projects.tags.models import Tag, TagType


def _ado_labels_on(feature: Feature) -> list[str]:
    return sorted(
        feature.tags.filter(type=TagType.AZURE_DEVOPS.value).values_list(
            "label", flat=True
        )
    )


@pytest.mark.django_db
def test_apply_initial_tag__pr_open__adds_pr_open_tag(
    azure_devops_configuration: AzureDevOpsConfiguration,
    azure_devops_pr_resource_open: FeatureExternalResource,
) -> None:
    # Given
    azure_devops_configuration.tagging_enabled = True
    azure_devops_configuration.save()

    # When
    apply_initial_tag(azure_devops_pr_resource_open)

    # Then
    assert _ado_labels_on(azure_devops_pr_resource_open.feature) == ["PR Open"]


@pytest.mark.django_db
def test_apply_initial_tag__work_item_open__adds_work_item_open_tag(
    azure_devops_configuration: AzureDevOpsConfiguration,
    azure_devops_work_item_resource_open: FeatureExternalResource,
) -> None:
    # Given
    azure_devops_configuration.tagging_enabled = True
    azure_devops_configuration.save()

    # When
    apply_initial_tag(azure_devops_work_item_resource_open)

    # Then
    assert _ado_labels_on(azure_devops_work_item_resource_open.feature) == [
        "Work Item Open"
    ]


@pytest.mark.django_db
def test_apply_initial_tag__tagging_disabled__no_op(
    azure_devops_configuration: AzureDevOpsConfiguration,
    azure_devops_pr_resource_open: FeatureExternalResource,
) -> None:
    # Given — tagging_enabled defaults to False
    assert azure_devops_configuration.tagging_enabled is False

    # When
    apply_initial_tag(azure_devops_pr_resource_open)

    # Then
    assert _ado_labels_on(azure_devops_pr_resource_open.feature) == []


@pytest.mark.django_db
def test_apply_initial_tag__no_configuration__no_op(
    azure_devops_pr_resource_open: FeatureExternalResource,
) -> None:
    # Given — no AzureDevOpsConfiguration exists for this project

    # When
    apply_initial_tag(azure_devops_pr_resource_open)

    # Then
    assert _ado_labels_on(azure_devops_pr_resource_open.feature) == []


@pytest.mark.django_db
def test_apply_initial_tag__pr_then_work_item__both_tags_coexist(
    azure_devops_configuration: AzureDevOpsConfiguration,
    azure_devops_pr_resource_open: FeatureExternalResource,
    azure_devops_work_item_resource_open: FeatureExternalResource,
) -> None:
    # Given
    azure_devops_configuration.tagging_enabled = True
    azure_devops_configuration.save()

    # When
    apply_initial_tag(azure_devops_pr_resource_open)
    apply_initial_tag(azure_devops_work_item_resource_open)

    # Then
    assert _ado_labels_on(azure_devops_pr_resource_open.feature) == [
        "PR Open",
        "Work Item Open",
    ]


@pytest.mark.django_db
def test_apply_initial_tag__pr_open_then_pr_merged__same_kind_is_replaced(
    azure_devops_configuration: AzureDevOpsConfiguration,
    azure_devops_pr_resource_open: FeatureExternalResource,
    azure_devops_pr_resource_merged: FeatureExternalResource,
) -> None:
    # Given
    azure_devops_configuration.tagging_enabled = True
    azure_devops_configuration.save()

    # When
    apply_initial_tag(azure_devops_pr_resource_open)
    apply_initial_tag(azure_devops_pr_resource_merged)

    # Then — the PR_OPEN tag was replaced by PR_MERGED
    assert _ado_labels_on(azure_devops_pr_resource_open.feature) == ["PR Merged"]


@pytest.mark.django_db
def test_clear_tag_for_resource__only_resource_of_kind__removes_tag(
    azure_devops_configuration: AzureDevOpsConfiguration,
    azure_devops_pr_resource_open: FeatureExternalResource,
) -> None:
    # Given
    azure_devops_configuration.tagging_enabled = True
    azure_devops_configuration.save()
    apply_initial_tag(azure_devops_pr_resource_open)
    assert _ado_labels_on(azure_devops_pr_resource_open.feature) == ["PR Open"]

    # When
    clear_tag_for_resource(azure_devops_pr_resource_open)

    # Then
    assert _ado_labels_on(azure_devops_pr_resource_open.feature) == []


@pytest.mark.django_db
def test_clear_tag_for_resource__other_resource_of_same_kind__keeps_tag(
    azure_devops_configuration: AzureDevOpsConfiguration,
    feature: Feature,
) -> None:
    # Given
    azure_devops_configuration.tagging_enabled = True
    azure_devops_configuration.save()
    first = FeatureExternalResource.objects.create(
        feature=feature,
        url="https://dev.azure.com/test-org/proj/_git/repo/pullrequest/1",
        type=ResourceType.AZURE_DEVOPS_PULL_REQUEST.value,
        metadata='{"state": "active", "is_draft": false}',
    )
    second = FeatureExternalResource.objects.create(
        feature=feature,
        url="https://dev.azure.com/test-org/proj/_git/repo/pullrequest/2",
        type=ResourceType.AZURE_DEVOPS_PULL_REQUEST.value,
        metadata='{"state": "active", "is_draft": false}',
    )
    apply_initial_tag(first)

    # When
    clear_tag_for_resource(first)

    # Then — the PR Open tag persists because `second` is still linked
    assert second.pk != first.pk
    assert _ado_labels_on(feature) == ["PR Open"]


@pytest.mark.django_db
def test_clear_tag_for_resource__different_kind__keeps_other_kinds_tag(
    azure_devops_configuration: AzureDevOpsConfiguration,
    azure_devops_pr_resource_open: FeatureExternalResource,
    azure_devops_work_item_resource_open: FeatureExternalResource,
) -> None:
    # Given
    azure_devops_configuration.tagging_enabled = True
    azure_devops_configuration.save()
    apply_initial_tag(azure_devops_pr_resource_open)
    apply_initial_tag(azure_devops_work_item_resource_open)

    # When — clear only the PR resource
    clear_tag_for_resource(azure_devops_pr_resource_open)

    # Then — Work Item tag persists
    assert _ado_labels_on(azure_devops_pr_resource_open.feature) == ["Work Item Open"]


@pytest.mark.django_db
def test_clear_tag_for_resource__non_ado_resource__leaves_gitlab_tag_intact(
    azure_devops_configuration: AzureDevOpsConfiguration,
    feature: Feature,
) -> None:
    # Given
    azure_devops_configuration.tagging_enabled = True
    azure_devops_configuration.save()
    gitlab_tag, _ = Tag.objects.get_or_create(
        label="Issue Open",
        project=feature.project,
        is_system_tag=True,
        type=TagType.GITLAB.value,
        defaults={"color": "#FC6D26", "description": "GitLab issue open"},
    )
    feature.tags.add(gitlab_tag)
    gitlab_resource = FeatureExternalResource.objects.create(
        feature=feature,
        url="https://gitlab.com/foo/bar/-/issues/1",
        type=ResourceType.GITLAB_ISSUE.value,
        metadata='{"state": "opened"}',
    )

    # When
    clear_tag_for_resource(gitlab_resource)

    # Then — no ADO tags appear AND the pre-existing GitLab tag survives
    assert _ado_labels_on(feature) == []
    assert sorted(
        feature.tags.filter(type=TagType.GITLAB.value).values_list("label", flat=True)
    ) == ["Issue Open"]


@pytest.mark.django_db
def test_refresh_tags_for_resource__state_change__rotates_tag(
    azure_devops_configuration: AzureDevOpsConfiguration,
    azure_devops_pr_resource_open: FeatureExternalResource,
) -> None:
    # Given
    azure_devops_configuration.tagging_enabled = True
    azure_devops_configuration.save()
    apply_initial_tag(azure_devops_pr_resource_open)
    assert _ado_labels_on(azure_devops_pr_resource_open.feature) == ["PR Open"]
    azure_devops_pr_resource_open.metadata = '{"state": "completed", "is_draft": false}'
    azure_devops_pr_resource_open.save()

    # When
    refresh_tags_for_resource(azure_devops_pr_resource_open)

    # Then
    assert _ado_labels_on(azure_devops_pr_resource_open.feature) == ["PR Merged"]


@pytest.mark.django_db
def test_refresh_tags_for_resource__unknown_state__no_op(
    azure_devops_configuration: AzureDevOpsConfiguration,
    azure_devops_pr_resource_open: FeatureExternalResource,
) -> None:
    # Given
    azure_devops_configuration.tagging_enabled = True
    azure_devops_configuration.save()
    apply_initial_tag(azure_devops_pr_resource_open)
    azure_devops_pr_resource_open.metadata = '{"state": "weird", "is_draft": false}'
    azure_devops_pr_resource_open.save()

    # When
    refresh_tags_for_resource(azure_devops_pr_resource_open)

    # Then — unknown state leaves the existing tag intact rather than
    # blindly clearing it.
    assert _ado_labels_on(azure_devops_pr_resource_open.feature) == ["PR Open"]
