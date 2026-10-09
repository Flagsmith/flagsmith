from typing import cast

import pytest
from rest_framework.test import APIClient

from features.dependencies.types import DependencyEdge
from tests.integration.types import AddFeaturePrerequisiteFixture


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
