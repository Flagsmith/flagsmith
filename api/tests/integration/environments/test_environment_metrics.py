from datetime import UTC, datetime, timedelta

import pytest
from django.conf import settings
from freezegun.api import FrozenDateTimeFactory
from rest_framework.test import APIClient

from features.future.types import UpdateFlagRequest
from features.models import Feature
from tests.types import ScheduleFlagChangeFixture


@pytest.mark.usefixtures("versioned_environment")
def test_get_environment_metrics__some_features_enabled__responds_200_with_feature_counts(
    admin_client: APIClient,
    environment_api_key: str,
    project: int,
) -> None:
    # Given
    checkout = Feature.objects.create(name="checkout", project_id=project)
    Feature.objects.create(name="payments", project_id=project)
    admin_client.patch(
        f"/api/__future__/environments/{environment_api_key}/features/{checkout.id}/",
        UpdateFlagRequest({"environment_default": {"enabled": True}}),
        format="json",
    )

    # When
    response = admin_client.get(
        f"/api/v1/environments/{environment_api_key}/metrics/",
    )

    # Then
    assert response.status_code == 200
    assert response.json() == {
        "metrics": [
            {
                "name": "total_features",
                "description": "Total features",
                "entity": "features",
                "rank": 1,
                "value": 2,
            },
            {
                "name": "enabled_features",
                "description": "Features enabled",
                "entity": "features",
                "rank": 2,
                "value": 1,
            },
            {
                "name": "segment_overrides",
                "description": "Segment overrides",
                "entity": "segments",
                "rank": 3,
                "value": 0,
            },
            {
                "name": "identity_overrides",
                "description": "Identity overrides",
                "entity": "identities",
                "rank": 4,
                "value": 0,
            },
        ]
    }


@pytest.mark.usefixtures("environment")
@pytest.mark.skipif(
    not settings.WORKFLOWS_LOGIC_INSTALLED,
    reason="workflows_logic module not installed (private package extra)",
)
def test_get_environment_metrics__feature_versioning_v1_with_superseded_versions__counts_live_enabled_state(
    admin_client: APIClient,
    environment_api_key: str,
    project: int,
    freezer: FrozenDateTimeFactory,
    schedule_flag_change: ScheduleFlagChangeFixture,
) -> None:
    # Given
    checkout = Feature.objects.create(name="checkout", project_id=project)
    admin_client.patch(
        f"/api/__future__/environments/{environment_api_key}/features/{checkout.id}/",
        UpdateFlagRequest({"environment_default": {"enabled": True}}),
        format="json",
    )
    tomorrow = datetime.now(tz=UTC) + timedelta(days=1)
    schedule_flag_change(feature_id=checkout.id, enabled=False, live_from=tomorrow)
    schedule_flag_change(
        feature_id=checkout.id, enabled=True, live_from=datetime.now(tz=UTC)
    )
    freezer.move_to(tomorrow + timedelta(minutes=1))

    # When
    response = admin_client.get(
        f"/api/v1/environments/{environment_api_key}/metrics/",
    )

    # Then
    assert response.status_code == 200
    assert response.json()["metrics"][1] == {
        "name": "enabled_features",
        "description": "Features enabled",
        "entity": "features",
        "rank": 2,
        "value": 0,
    }
