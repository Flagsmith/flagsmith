from unittest.mock import MagicMock

import pytest
from django.conf import settings

from features.feature_external_resources.models import FeatureExternalResource
from integrations.github.github import post_comment_to_github


@pytest.mark.django_db
def test_after_save_hook(mocker, feature, github_configuration):
    feature_resource = FeatureExternalResource.objects.create(
        url="https://github.com/example/example-repo/issues/1",
        type="GITHUB_ISSUE",
        feature=feature,
    )
    settings.GITHUB_PEM = "GITHUB_PEM"

    mocked_function = MagicMock()
    mocked_function = mocker.patch(
        "integrations.github.tasks.call_github_app_webhook_for_feature_state"
    )
    mocked_function.return_value = True

    mocked_post = MagicMock()
    mocked_post.return_value.status_code = 200
    mocker.patch("integrations.github.github.post_comment_to_github", mocked_post)

    post_comment_to_github("installation_id", "owner", "repo", "issue", "body")

    assert mocked_post.called

    feature_resource.exectute_after_save_actions()

    assert mocked_function.called
