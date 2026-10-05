import json
from datetime import UTC, datetime, timedelta

import pytest
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from freezegun.api import FrozenDateTimeFactory
from rest_framework.test import APIClient

from features.future.types import UpdateFlagRequest
from features.import_export.types import FeatureExportData
from features.models import Feature
from tests.types import ScheduleFlagChangeFixture


@pytest.mark.skipif(
    not settings.WORKFLOWS_LOGIC_INSTALLED,
    reason="workflows_logic module not installed (private package extra)",
)
def test_import_features__overwrite_flag_edited_while_change_was_scheduled__serves_imported_flag(
    admin_client: APIClient,
    environment: int,
    environment_api_key: str,
    project: int,
    freezer: FrozenDateTimeFactory,
    schedule_flag_change: ScheduleFlagChangeFixture,
    sdk_client: APIClient,
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
    response = admin_client.post(
        f"/api/v1/features/feature-import/{environment}",
        {
            "strategy": "OVERWRITE_DESTRUCTIVE",
            "file": SimpleUploadedFile(
                "features.json",
                json.dumps(
                    [
                        FeatureExportData(
                            {
                                "name": "checkout",
                                "default_enabled": False,
                                "is_server_key_only": False,
                                "initial_value": None,
                                "value": "imported",
                                "type": "unicode",
                                "enabled": True,
                                "multivariate": [],
                            }
                        )
                    ]
                ).encode(),
            ),
        },
        format="multipart",
    )

    # Then
    assert response.status_code == 201
    [flag] = sdk_client.get("/api/v1/flags/").json()
    assert flag["enabled"] is True
    assert flag["feature_state_value"] == "imported"
