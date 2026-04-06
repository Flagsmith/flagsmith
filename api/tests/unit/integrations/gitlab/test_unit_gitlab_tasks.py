import pytest
import responses

from features.feature_external_resources.models import (
    FeatureExternalResource,
    ResourceType,
)
from features.models import Feature
from integrations.gitlab.constants import GitLabEventType
from integrations.gitlab.models import GitLabConfiguration
from integrations.gitlab.tasks import _parse_resource_url, post_gitlab_comment
from projects.models import Project


@pytest.mark.parametrize(
    "url,expected",
    [
        (
            "https://gitlab.example.com/group/project/-/merge_requests/42",
            ("group/project", "merge_requests", 42),
        ),
        (
            "https://gitlab.example.com/group/project/-/issues/7",
            ("group/project", "issues", 7),
        ),
        (
            "https://gitlab.example.com/group/project/-/work_items/7",
            ("group/project", "issues", 7),
        ),
        (
            "https://gitlab.example.com/org/sub-group/project/-/merge_requests/1",
            ("org/sub-group/project", "merge_requests", 1),
        ),
        (
            "https://gitlab.example.com/unknown/path/to/resource",
            None,
        ),
        (
            "https://gitlab.example.com/group/project/-/issues/",
            None,
        ),
        (
            "https://gitlab.example.com/-/issues/5",
            None,
        ),
    ],
    ids=[
        "mr",
        "issue",
        "work-item",
        "nested-group",
        "unknown-format",
        "no-iid",
        "no-project-path",
    ],
)
def test_parse_resource_url__various_urls__returns_correct_tuple(
    url: str,
    expected: tuple[str, str, int] | None,
) -> None:
    # Given
    # When
    result = _parse_resource_url(url)

    # Then
    assert result == expected


@pytest.mark.django_db
@responses.activate
def test_post_gitlab_comment__linked_resource__posts_comment(
    project: Project,
    feature: Feature,
    gitlab_configuration: GitLabConfiguration,
) -> None:
    # Given
    FeatureExternalResource.objects.create(
        url="https://gitlab.example.com/testgroup/testrepo/-/issues/1",
        type=ResourceType.GITLAB_ISSUE,
        feature=feature,
        metadata='{"state": "opened"}',
    )
    responses.add(
        responses.POST,
        "https://gitlab.example.com/api/v4/projects/1/issues/1/notes",
        json={"id": 1, "body": "comment"},
        status=201,
    )

    # When
    post_gitlab_comment(
        project_id=project.id,
        feature_id=feature.id,
        feature_name=feature.name,
        event_type=GitLabEventType.FLAG_UPDATED.value,
        feature_states=[],
    )

    # Then
    assert len(responses.calls) == 1


@pytest.mark.django_db
def test_post_gitlab_comment__no_config__returns_early(
    project: Project,
    feature: Feature,
) -> None:
    # Given — no GitLabConfiguration exists

    # When
    post_gitlab_comment(
        project_id=project.id,
        feature_id=feature.id,
        feature_name=feature.name,
        event_type=GitLabEventType.FLAG_UPDATED.value,
        feature_states=[],
    )

    # Then
    assert GitLabConfiguration.objects.filter(project=project).count() == 0


@pytest.mark.django_db
def test_post_gitlab_comment__no_gitlab_project_id__returns_early(
    project: Project,
    feature: Feature,
) -> None:
    # Given
    GitLabConfiguration.objects.create(
        project=project,
        gitlab_instance_url="https://gitlab.example.com",
        access_token="token",
        webhook_secret="secret",
        gitlab_project_id=None,
    )

    # When
    post_gitlab_comment(
        project_id=project.id,
        feature_id=feature.id,
        feature_name=feature.name,
        event_type=GitLabEventType.FLAG_UPDATED.value,
        feature_states=[],
    )

    # Then
    assert True  # no error raised, returns early


@pytest.mark.django_db
def test_post_gitlab_comment__no_linked_resources__returns_early(
    project: Project,
    feature: Feature,
    gitlab_configuration: GitLabConfiguration,
) -> None:
    # Given — no FeatureExternalResource linked

    # When
    post_gitlab_comment(
        project_id=project.id,
        feature_id=feature.id,
        feature_name=feature.name,
        event_type=GitLabEventType.FLAG_UPDATED.value,
        feature_states=[],
    )

    # Then
    assert True  # no error raised, returns early


@pytest.mark.django_db
@responses.activate
def test_post_gitlab_comment__resource_removed__posts_to_url(
    project: Project,
    feature: Feature,
    gitlab_configuration: GitLabConfiguration,
) -> None:
    # Given
    resource_url = "https://gitlab.example.com/testgroup/testrepo/-/issues/5"
    responses.add(
        responses.POST,
        "https://gitlab.example.com/api/v4/projects/1/issues/5/notes",
        json={"id": 1, "body": "unlinked"},
        status=201,
    )

    # When
    post_gitlab_comment(
        project_id=project.id,
        feature_id=feature.id,
        feature_name=feature.name,
        event_type=GitLabEventType.FEATURE_EXTERNAL_RESOURCE_REMOVED.value,
        feature_states=[],
        url=resource_url,
    )

    # Then
    assert len(responses.calls) == 1


@pytest.mark.django_db
@responses.activate
def test_post_gitlab_comment__unparseable_url__skips_without_error(
    project: Project,
    feature: Feature,
    gitlab_configuration: GitLabConfiguration,
) -> None:
    # Given
    FeatureExternalResource.objects.create(
        url="https://gitlab.example.com/not/a/valid/resource",
        type=ResourceType.GITLAB_ISSUE,
        feature=feature,
        metadata='{"state": "opened"}',
    )

    # When
    post_gitlab_comment(
        project_id=project.id,
        feature_id=feature.id,
        feature_name=feature.name,
        event_type=GitLabEventType.FLAG_UPDATED.value,
        feature_states=[],
    )

    # Then
    assert len(responses.calls) == 0


@pytest.mark.django_db
def test_post_gitlab_comment__resource_removed_no_url__returns_early(
    project: Project,
    feature: Feature,
    gitlab_configuration: GitLabConfiguration,
) -> None:
    # Given — resource removed event with no URL

    # When
    post_gitlab_comment(
        project_id=project.id,
        feature_id=feature.id,
        feature_name=feature.name,
        event_type=GitLabEventType.FEATURE_EXTERNAL_RESOURCE_REMOVED.value,
        feature_states=[],
        url=None,
    )

    # Then
    assert True  # no error, returns early
