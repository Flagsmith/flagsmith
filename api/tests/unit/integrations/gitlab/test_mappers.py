from unittest.mock import Mock

from features.feature_external_resources.models import ResourceType
from integrations.gitlab.mappers import map_gitlab_resource_to_tag_label


def test_map_gitlab_resource_to_tag_label__non_gitlab_type__returns_none() -> None:
    # Given — a non-GitLab resource type reaches the mapper defensively.
    resource = Mock(type=ResourceType.GITHUB_ISSUE.value, metadata='{"state": "open"}')

    # When
    result = map_gitlab_resource_to_tag_label(resource)

    # Then
    assert result is None
