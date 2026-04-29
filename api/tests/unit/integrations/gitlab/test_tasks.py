from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
import pytest_mock
import responses
from pytest_structlog import StructuredLogCapture

from features.feature_external_resources.models import FeatureExternalResource
from features.models import Feature, FeatureState
from integrations.gitlab.models import GitLabConfiguration
from integrations.gitlab.tasks import (
    apply_gitlab_label,
    post_gitlab_feature_deleted_comment,
    post_gitlab_linked_comment,
    post_gitlab_state_change_comment,
    post_gitlab_unlinked_comment,
    remove_gitlab_label,
)

if TYPE_CHECKING:
    from projects.models import Project


@pytest.mark.django_db
def test_post_gitlab_linked_comment_task__resource_missing__noop(
    mocker: pytest_mock.MockerFixture,
) -> None:
    # Given
    mock_post = mocker.patch(
        "integrations.gitlab.services.comments.post_linked_comment",
    )

    # When
    post_gitlab_linked_comment(resource_id=999_999)

    # Then
    mock_post.assert_not_called()


def test_post_gitlab_unlinked_comment_task__called__delegates_to_service(
    mocker: pytest_mock.MockerFixture,
) -> None:
    # Given
    mock_post = mocker.patch(
        "integrations.gitlab.tasks.post_unlinked_comment",
    )

    # When
    post_gitlab_unlinked_comment(
        feature_name="show_new_checkout",
        feature_id=99,
        resource_url="https://gitlab.example.com/org/repo/-/issues/1",
        resource_type="GITLAB_ISSUE",
        project_id=42,
    )

    # Then
    mock_post.assert_called_once_with(
        feature_name="show_new_checkout",
        feature_id=99,
        resource_url="https://gitlab.example.com/org/repo/-/issues/1",
        resource_type="GITLAB_ISSUE",
        project_id=42,
    )


@pytest.mark.django_db
def test_post_gitlab_state_change_comment_task__feature_state_missing__noop(
    mocker: pytest_mock.MockerFixture,
) -> None:
    # Given
    mock_post = mocker.patch(
        "integrations.gitlab.tasks.post_state_change_comment",
    )

    # When
    post_gitlab_state_change_comment(feature_state_id=999_999)

    # Then
    mock_post.assert_not_called()


@pytest.mark.django_db
def test_post_gitlab_state_change_comment_task__called__delegates_to_service(
    mocker: pytest_mock.MockerFixture,
    feature_state: FeatureState,
) -> None:
    # Given
    mock_post = mocker.patch(
        "integrations.gitlab.tasks.post_state_change_comment",
    )

    # When
    post_gitlab_state_change_comment(feature_state_id=feature_state.id)

    # Then
    mock_post.assert_called_once()
    [call_args] = mock_post.call_args_list
    assert call_args.args[0].id == feature_state.id


def test_post_gitlab_feature_deleted_comment_task__called__delegates_to_service(
    mocker: pytest_mock.MockerFixture,
) -> None:
    # Given
    mock_post = mocker.patch(
        "integrations.gitlab.tasks.post_feature_deleted_comment",
    )

    # When
    post_gitlab_feature_deleted_comment(
        feature_name="show_new_checkout",
        feature_id=99,
        project_id=42,
    )

    # Then
    mock_post.assert_called_once_with(
        feature_name="show_new_checkout",
        feature_id=99,
        project_id=42,
    )


@pytest.mark.django_db
def test_apply_gitlab_label__resource_missing__noop(
    mocker: pytest_mock.MockerFixture,
) -> None:
    # Given
    mock_apply = mocker.patch(
        "integrations.gitlab.tasks.apply_flagsmith_label_to_resource",
    )

    # When
    apply_gitlab_label(resource_id=999_999)

    # Then
    mock_apply.assert_not_called()


@pytest.mark.django_db
def test_apply_gitlab_label__resource_exists__calls_apply_flagsmith_label(
    mocker: pytest_mock.MockerFixture,
    feature: Feature,
) -> None:
    # Given
    resource = FeatureExternalResource.objects.create(
        url="https://gitlab.example.com/testorg/testrepo/-/issues/1",
        type="GITLAB_ISSUE",
        feature=feature,
    )
    mock_apply = mocker.patch(
        "integrations.gitlab.tasks.apply_flagsmith_label_to_resource",
    )

    # When
    apply_gitlab_label(resource_id=resource.id)

    # Then
    mock_apply.assert_called_once()
    [call_args] = mock_apply.call_args_list
    assert call_args.args[0].id == resource.id


@pytest.mark.django_db
def test_remove_gitlab_label__unparseable_url__noop(
    project: Project,
) -> None:
    # Given
    config = GitLabConfiguration.objects.create(
        project=project,
        gitlab_instance_url="https://gitlab.example.com",
        access_token="glpat-test-token",
        labeling_enabled=True,
    )

    # When
    remove_gitlab_label(
        project_id=config.project_id,
        feature_id=0,
        resource_pk=0,
        resource_url="https://gitlab.example.com/not-a-resource",
        resource_type="GITLAB_ISSUE",
    )

    # Then
    assert GitLabConfiguration.objects.filter(project=project).exists()


@pytest.mark.django_db
def test_remove_gitlab_label__another_resource_exists__noop(
    project: Project,
    feature: Feature,
) -> None:
    # Given
    GitLabConfiguration.objects.create(
        project=project,
        gitlab_instance_url="https://gitlab.example.com",
        access_token="glpat-test-token",
        labeling_enabled=True,
    )
    url = "https://gitlab.example.com/testorg/testrepo/-/issues/1"
    resource = FeatureExternalResource.objects.create(
        url=url,
        type="GITLAB_ISSUE",
        feature=feature,
    )
    other = FeatureExternalResource.objects.create(
        url=url,
        type="GITLAB_ISSUE",
        feature=Feature.objects.create(
            name="other_flag",
            project=project,
            initial_value="",
        ),
    )

    # When
    remove_gitlab_label(
        project_id=project.id,
        feature_id=feature.id,
        resource_pk=resource.pk,
        resource_url=url,
        resource_type="GITLAB_ISSUE",
    )

    # Then
    assert FeatureExternalResource.objects.filter(pk=other.pk).exists()


@pytest.mark.django_db
@responses.activate
@pytest.mark.parametrize(
    "api_status, expected_event",
    [
        (200, "label.removed"),
        (500, "label.removal_failed"),
    ],
    ids=["success", "api_failure"],
)
def test_remove_gitlab_label__last_resource__calls_api_and_logs(
    project: Project,
    feature: Feature,
    log: StructuredLogCapture,
    api_status: int,
    expected_event: str,
) -> None:
    # Given
    GitLabConfiguration.objects.create(
        project=project,
        gitlab_instance_url="https://gitlab.example.com",
        access_token="glpat-test-token",
        labeling_enabled=True,
    )
    responses.put(
        "https://gitlab.example.com/api/v4/projects/testorg%2Ftestrepo/issues/1",
        json={"iid": 1},
        status=api_status,
    )

    # When
    remove_gitlab_label(
        project_id=project.id,
        feature_id=feature.id,
        resource_pk=0,
        resource_url="https://gitlab.example.com/testorg/testrepo/-/issues/1",
        resource_type="GITLAB_ISSUE",
    )

    # Then
    assert len(responses.calls) == 1
    assert any(e["event"] == expected_event for e in log.events)
