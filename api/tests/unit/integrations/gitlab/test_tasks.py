import pytest
import pytest_mock

from integrations.gitlab.tasks import (
    post_gitlab_linked_comment,
    post_gitlab_unlinked_comment,
)


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
