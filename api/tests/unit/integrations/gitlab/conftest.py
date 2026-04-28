from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from integrations.gitlab.models import GitLabConfiguration

if TYPE_CHECKING:
    from projects.models import Project


@pytest.fixture()
def gitlab_config(project: Project) -> GitLabConfiguration:
    return GitLabConfiguration.objects.create(  # type: ignore[no-any-return]
        project=project,
        gitlab_instance_url="https://gitlab.example.com",
        access_token="glpat-test-token",
    )
