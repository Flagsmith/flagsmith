import uuid

import pytest
from common.projects.permissions import (
    CREATE_FEATURE,
    VIEW_PROJECT,
)
from django.urls import reverse
from pytest_lazyfixture import lazy_fixture  # type: ignore[import-untyped]
from rest_framework import status
import json
from features.multivariate.views import MultivariateFeatureOptionViewSet
from projects.permissions import NestedProjectPermissions
from unittest.mock import Mock
from features.multivariate.views import MultivariateFeatureOptionPermissions
from common.environments.permissions import UPDATE_FEATURE_STATE, VIEW_ENVIRONMENT
from features.multivariate.models import MultivariateFeatureOption


@pytest.mark.parametrize(
    "action,expected_permission",
    [
        ("list", VIEW_PROJECT),
        ("retrieve", VIEW_PROJECT),
        ("create", CREATE_FEATURE),
        ("destroy", CREATE_FEATURE),
    ],
)
def test_multivariate_feature_option_permissions_project_actions(
    action, expected_permission
):  # type: ignore[no-untyped-def]
    # Given
    permission = MultivariateFeatureOptionPermissions()
    request = Mock()
    request.user.has_project_permission.return_value = True
    view = Mock()
    obj = Mock()
    obj.feature.project = Mock()

    view.action = action

    # When
    result = permission.has_object_permission(request, view, obj)

    # Then
    assert result is True
    request.user.has_project_permission.assert_called_with(
        expected_permission, obj.feature.project
    )


@pytest.mark.parametrize("action", ["update", "partial_update"])
def test_multivariate_feature_option_permissions_environment_actions(
    db,
    action,
    environment,
    staff_client,
    project,
    feature,
    mv_option_50_percent,
    with_environment_permissions,
):
    # Given - user has UPDATE_FEATURE_STATE permission
    with_environment_permissions(
        [VIEW_ENVIRONMENT, UPDATE_FEATURE_STATE], environment.id
    )  # type: ignore[call-arg]

    url = reverse(
        "api-v1:projects:feature-mv-options-detail",
        args=[
            project.id,
            feature.id,
            mv_option_50_percent,
        ],
    )

    data = {
        "environment_id": environment.api_key,
        "boolean_value": None,
        "default_percentage_allocation": 50.0,
        "feature": feature.id,
        "integer_value": None,
        "string_value": "updated value",
        "type": "unicode",
    }
    # When
    response = staff_client.put(url, json.dumps(data), content_type="application/json")

    # Then
    assert response.status_code == 200


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_get_mv_feature_option_by_uuid(client, project, multivariate_feature):  # type: ignore[no-untyped-def]
    # Given
    mv_option_uuid = multivariate_feature.multivariate_options.first().uuid
    url = reverse(
        "api-v1:multivariate:get-mv-feature-option-by-uuid", args=[str(mv_option_uuid)]
    )

    # When
    response = client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.data["uuid"] == str(mv_option_uuid)
    assert response.data["feature"] == multivariate_feature.id


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_get_mv_feature_option_by_uuid_returns_404_if_mv_option_does_not_exists(  # type: ignore[no-untyped-def]
    client, project
):
    # Given
    url = reverse(
        "api-v1:multivariate:get-mv-feature-option-by-uuid", args=[str(uuid.uuid4())]
    )

    # When
    response = client.get(url)

    # Then
    assert response.status_code == status.HTTP_404_NOT_FOUND
