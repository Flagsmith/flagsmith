import pytest

from features.feature_external_resources.models import (
    FeatureExternalResource,
    ResourceType,
)
from features.models import Feature
from integrations.gitlab.services.tagging import (
    apply_initial_tag,
    clear_tag_for_resource,
)
from projects.models import Project
from projects.tags.models import Tag, TagType


@pytest.mark.django_db
def test_clear_tag_for_resource__only_resource_of_kind__removes_tag(
    feature: Feature,
) -> None:
    # Given
    resource = FeatureExternalResource.objects.create(
        feature=feature,
        url="https://gitlab.example.com/testorg/testrepo/-/issues/1",
        type=ResourceType.GITLAB_ISSUE.value,
        metadata='{"state": "opened"}',
    )
    apply_initial_tag(resource)
    assert sorted(
        feature.tags.filter(type=TagType.GITLAB.value).values_list("label", flat=True)
    ) == ["Issue Open"]

    # When
    clear_tag_for_resource(resource)

    # Then
    assert (
        sorted(
            feature.tags.filter(type=TagType.GITLAB.value).values_list(
                "label", flat=True
            )
        )
        == []
    )


@pytest.mark.django_db
def test_clear_tag_for_resource__other_resource_of_same_kind_remains__keeps_tag(
    feature: Feature,
) -> None:
    # Given
    first = FeatureExternalResource.objects.create(
        feature=feature,
        url="https://gitlab.example.com/testorg/testrepo/-/issues/1",
        type=ResourceType.GITLAB_ISSUE.value,
        metadata='{"state": "opened"}',
    )
    FeatureExternalResource.objects.create(
        feature=feature,
        url="https://gitlab.example.com/testorg/testrepo/-/issues/2",
        type=ResourceType.GITLAB_ISSUE.value,
        metadata='{"state": "opened"}',
    )
    apply_initial_tag(first)
    assert sorted(
        feature.tags.filter(type=TagType.GITLAB.value).values_list("label", flat=True)
    ) == ["Issue Open"]

    # When
    clear_tag_for_resource(first)

    # Then
    assert sorted(
        feature.tags.filter(type=TagType.GITLAB.value).values_list("label", flat=True)
    ) == ["Issue Open"]


@pytest.mark.django_db
def test_clear_tag_for_resource__different_kind_remains__keeps_other_kind_tag(
    feature: Feature,
) -> None:
    # Given
    issue = FeatureExternalResource.objects.create(
        feature=feature,
        url="https://gitlab.example.com/testorg/testrepo/-/issues/1",
        type=ResourceType.GITLAB_ISSUE.value,
        metadata='{"state": "opened"}',
    )
    mr = FeatureExternalResource.objects.create(
        feature=feature,
        url="https://gitlab.example.com/testorg/testrepo/-/merge_requests/7",
        type=ResourceType.GITLAB_MR.value,
        metadata='{"state": "opened"}',
    )
    apply_initial_tag(issue)
    apply_initial_tag(mr)
    assert sorted(
        feature.tags.filter(type=TagType.GITLAB.value).values_list("label", flat=True)
    ) == ["Issue Open", "MR Open"]

    # When
    clear_tag_for_resource(issue)

    # Then
    assert sorted(
        feature.tags.filter(type=TagType.GITLAB.value).values_list("label", flat=True)
    ) == ["MR Open"]


@pytest.mark.django_db
def test_clear_tag_for_resource__non_gitlab_type__leaves_tags_intact(
    feature: Feature,
    project: Project,
) -> None:
    # Given — feature has both a GitHub tag and a GitLab tag already.
    expected_tags = [
        ("Issue Open", TagType.GITHUB.value),
        ("Issue Open", TagType.GITLAB.value),
    ]

    github_tag = Tag.objects.create(
        label="Issue Open",
        project=project,
        type=TagType.GITHUB.value,
        is_system_tag=True,
    )
    gitlab_issue = FeatureExternalResource.objects.create(
        feature=feature,
        url="https://gitlab.example.com/testorg/testrepo/-/issues/1",
        type=ResourceType.GITLAB_ISSUE.value,
        metadata='{"state": "opened"}',
    )
    apply_initial_tag(gitlab_issue)
    feature.tags.add(github_tag)
    assert sorted(feature.tags.values_list("label", "type")) == expected_tags

    # When — clearing for a GitHub FER
    github_resource = FeatureExternalResource(
        feature=feature,
        url="https://github.com/testorg/testrepo/issues/1",
        type=ResourceType.GITHUB_ISSUE.value,
    )
    clear_tag_for_resource(github_resource)

    # Then — must not touch either tag
    assert sorted(feature.tags.values_list("label", "type")) == expected_tags
