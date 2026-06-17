from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import pytest

from integrations.gitlab.models import GitLabConfiguration, GitLabWebhook

if TYPE_CHECKING:
    from projects.models import Project


@pytest.fixture()
def gitlab_config(project: Project) -> GitLabConfiguration:
    return GitLabConfiguration.objects.create(  # type: ignore[no-any-return]
        project=project,
        gitlab_instance_url="https://gitlab.example.com",
        access_token="glpat-test-token",
    )


@pytest.fixture()
def gitlab_webhook(gitlab_config: GitLabConfiguration) -> GitLabWebhook:
    return GitLabWebhook.objects.create(  # type: ignore[no-any-return]
        uuid=uuid.uuid4(),
        gitlab_configuration=gitlab_config,
        gitlab_project_id=42,
        gitlab_path_with_namespace="testorg/testrepo",
        gitlab_hook_id=1,
        secret="topsecret",
    )
