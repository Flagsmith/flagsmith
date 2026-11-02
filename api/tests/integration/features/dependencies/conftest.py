from datetime import datetime
from typing import cast

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from features.dependencies.types import DependencyEdge
from features.workflows.core.models import ChangeRequest
from tests.integration.types import (
    AddFeaturePrerequisiteFixture,
    CreateChangeRequestFixture,
)


@pytest.fixture
def add_feature_prerequisite(admin_client: APIClient) -> AddFeaturePrerequisiteFixture:
    def _add_feature_prerequisite(
        environment_api_key: str,
        feature_id: int,
        prerequisite_feature_id: int,
    ) -> DependencyEdge:
        response = admin_client.post(
            f"/api/v1/environments/{environment_api_key}/features/{feature_id}/dependencies/{prerequisite_feature_id}/",
        )
        assert response.status_code == 201
        return cast(DependencyEdge, response.json())

    return _add_feature_prerequisite


@pytest.fixture
def create_change_request(
    admin_client: APIClient,
    environment_api_key: str,
) -> CreateChangeRequestFixture:
    def _create_change_request(
        feature_id: int,
        title: str,
        live_from: datetime | None = None,
    ) -> ChangeRequest:
        response = admin_client.post(
            f"/api/v1/environments/{environment_api_key}/create-change-request/",
            {
                "title": title,
                "feature_states": [],
                "change_sets": [
                    {
                        "feature": feature_id,
                        "live_from": (live_from or timezone.now()).isoformat(),
                        "feature_states_to_create": [],
                        "feature_states_to_update": [],
                        "segment_ids_to_delete_overrides": [],
                    }
                ],
            },
            format="json",
        )
        return ChangeRequest.objects.get(id=response.json()["id"])  # type: ignore[no-any-return]

    return _create_change_request
