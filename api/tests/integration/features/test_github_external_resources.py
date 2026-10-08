import json
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest
import responses
from django.conf import settings
from freezegun.api import FrozenDateTimeFactory
from rest_framework.test import APIClient

from features.future.types import UpdateFlagRequest
from features.models import Feature
from integrations.github.models import GithubConfiguration, GitHubRepository
from projects.models import Project
from tests.types import ScheduleFlagChangeFixture


@pytest.mark.freeze_time("2026-10-06T09:00:00Z")
@pytest.mark.skipif(
    not settings.WORKFLOWS_LOGIC_INSTALLED,
    reason="workflows_logic module not installed (private package extra)",
)
@responses.activate
def test_create_external_resource__github_issue_for_flag_edited_while_change_was_scheduled__comments_served_flag(
    admin_client: APIClient,
    environment: int,
    environment_api_key: str,
    project: int,
    freezer: FrozenDateTimeFactory,
    schedule_flag_change: ScheduleFlagChangeFixture,
    mock_github_client_generate_token: MagicMock,
) -> None:
    # Given
    checkout = Feature.objects.create(name="checkout", project_id=project)
    tomorrow = datetime.now(tz=UTC) + timedelta(days=1)
    freezer.tick(timedelta(minutes=1))
    admin_client.patch(
        f"/api/__future__/environments/{environment_api_key}/features/{checkout.id}/",
        UpdateFlagRequest({"environment_default": {"enabled": True}}),
        format="json",
    )
    freezer.tick(timedelta(minutes=1))
    schedule_flag_change(feature_id=checkout.id, enabled=False, live_from=tomorrow)
    freezer.tick(timedelta(minutes=1))
    schedule_flag_change(
        feature_id=checkout.id, enabled=True, live_from=datetime.now(tz=UTC)
    )
    freezer.move_to(tomorrow + timedelta(minutes=1))
    project_instance = Project.objects.get(id=project)
    GitHubRepository.objects.create(
        github_configuration=GithubConfiguration.objects.create(
            organisation=project_instance.organisation,
            installation_id="1234567",
        ),
        repository_owner="flagsmith",
        repository_name="storefront",
        project=project_instance,
    )
    responses.post(
        "https://api.github.com/repos/flagsmith/storefront/issues/42/comments",
        json={"id": 1},
        status=201,
    )

    # When
    response = admin_client.post(
        f"/api/v1/projects/{project}/features/{checkout.id}/feature-external-resources/",
        data={
            "type": "GITHUB_ISSUE",
            "url": "https://github.com/flagsmith/storefront/issues/42",
            "feature": checkout.id,
            "metadata": {
                "draft": False,
                "merged": False,
                "state": "open",
                "title": "Roll out the new checkout",
            },
        },
        format="json",
    )

    # Then
    assert response.status_code == 201
    [comment_call] = responses.calls
    assert json.loads(comment_call.request.body) == {
        "body": (
            "**Flagsmith feature linked:** `checkout`\n"
            "Default Values:\n"
            "| Environment | Enabled | Value | Last Updated (UTC) |\n"
            "| :--- | :----- | :------ | :------ |\n"
            f"| [Test Environment](https://example.com/project/{project}/environment/{environment_api_key}/features?feature={checkout.id}&tab=value)"
            " | ❌ Disabled |  | 2026-10-06 09:02:00 |\n"
        ),
    }
