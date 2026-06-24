"""
Shared fixtures for the flagd integration suite.

The endpoints are opt-in per project, so every integration test here
needs the project's ``FlagdProjectConfiguration`` row present and
``enabled``. Doing it via ``autouse`` keeps test bodies focused on the
behaviour under test rather than the integration's enablement state.
"""

from __future__ import annotations

import pytest

from integrations.flagd.models import FlagdProjectConfiguration


@pytest.fixture(autouse=True)
def enable_flagd_for_project(project: int) -> None:
    """Ensure flagd is enabled for the test project."""
    FlagdProjectConfiguration.objects.update_or_create(
        project_id=project, defaults={"enabled": True}
    )
