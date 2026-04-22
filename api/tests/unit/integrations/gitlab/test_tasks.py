import pytest
import pytest_mock

from integrations.gitlab.tasks import post_gitlab_linked_comment


@pytest.mark.django_db
def test_post_gitlab_linked_comment_task__resource_missing__noop(
    mocker: pytest_mock.MockerFixture,
) -> None:
    # Given — task fires after the resource was deleted.
    mock_post = mocker.patch(
        "integrations.gitlab.services.comments.post_linked_comment",
    )

    # When
    post_gitlab_linked_comment(resource_id=999_999)

    # Then
    mock_post.assert_not_called()
