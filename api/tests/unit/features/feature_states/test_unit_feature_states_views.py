import json

import pytest
from common.environments.permissions import UPDATE_FEATURE_STATE
from django.urls import reverse
from pytest_lazyfixture import lazy_fixture  # type: ignore[import-untyped]
from rest_framework import status
from rest_framework.test import APIClient

from environments.models import Environment
from features.models import Feature
from features.versioning.versioning_service import (
    get_environment_flags_list,
)
from tests.types import WithEnvironmentPermissionsCallable


@pytest.mark.parametrize(
    "environment_",
    (lazy_fixture("environment"), lazy_fixture("environment_v2_versioning")),
)
def test_update_flag(
    staff_client: APIClient,
    feature: Feature,
    environment_: Environment,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
) -> None:
    # Given
    with_environment_permissions([UPDATE_FEATURE_STATE])  # type: ignore[call-arg]
    url = reverse(
        "api-v1:environments:update-flag",
        kwargs={"environment_id": environment_.id, "feature_name": feature.name},
    )

    data = {"enabled": True, "feature_state_value": "42", "type": "int"}

    # When
    response = staff_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK

    latest_flags = get_environment_flags_list(
        environment=environment_, feature_name=feature.name
    )

    assert latest_flags[0].enabled is True
    assert latest_flags[0].get_feature_state_value() == 42
