import json
import uuid

import pytest
from common.projects.permissions import (
    CREATE_FEATURE,
    VIEW_PROJECT,
)
from django.urls import reverse
from pytest_lazy_fixtures import lf as lazy_fixture
from rest_framework import status
from rest_framework.test import APIClient

from features.models import Feature
from features.multivariate.models import MultivariateFeatureOption
from features.multivariate.views import MultivariateFeatureOptionViewSet
from projects.models import Project
from projects.permissions import NestedProjectPermissions


def test_multivariate_feature_options_view_set__get_permissions__returns_expected_permissions():  # type: ignore[no-untyped-def]
    # Given
    view_set = MultivariateFeatureOptionViewSet()

    # When
    permissions = view_set.get_permissions()  # type: ignore[no-untyped-call]

    # Then
    assert len(permissions) == 1
    assert isinstance(permissions[0], NestedProjectPermissions)
    assert permissions[0].action_permission_map == {
        "list": VIEW_PROJECT,
        "detail": VIEW_PROJECT,
        "create": CREATE_FEATURE,
        "update": CREATE_FEATURE,
        "partial_update": CREATE_FEATURE,
        "destroy": CREATE_FEATURE,
    }


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_get_mv_feature_option_by_uuid__valid_uuid__returns_option(  # type: ignore[no-untyped-def]
    client, project, multivariate_feature
):
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
def test_get_mv_feature_option_by_uuid__nonexistent_uuid__returns_404(  # type: ignore[no-untyped-def]
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


def test_list_mv_options__feature_in_other_project__returns_404(
    admin_client: APIClient,
    project: Project,
    organisation_two_project_one: Project,
) -> None:
    # Given
    feature = Feature.objects.create(
        name="feature",
        project=organisation_two_project_one,
        type="MULTIVARIATE",
        initial_value="control",
    )
    for percentage_allocation in (30, 30, 40):
        MultivariateFeatureOption.objects.create(
            feature=feature,
            default_percentage_allocation=percentage_allocation,
            type="unicode",
            string_value=f"multivariate option for {percentage_allocation}%",
        )

    url = f"/api/v1/projects/{project.id}/features/{feature.id}/mv-options/"

    # When
    response = admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_create_mv_option__no_percentage_allocation__defaults_to_model_default(
    admin_client: APIClient,
    project: Project,
    feature: Feature,
) -> None:
    # Given
    url = reverse(
        "api-v1:projects:feature-mv-options-list", args=[project.id, feature.id]
    )
    data = {"type": "unicode", "feature": feature.id, "string_value": "bigger"}

    # When
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["default_percentage_allocation"] == 100


def test_create_mv_option__no_percentage_allocation_with_siblings__returns_bad_request(
    admin_client: APIClient,
    project: Project,
    multivariate_feature: Feature,
) -> None:
    # Given - the existing options already use 100%, so the default of 100 overflows
    url = reverse(
        "api-v1:projects:feature-mv-options-list",
        args=[project.id, multivariate_feature.id],
    )
    data = {
        "type": "unicode",
        "feature": multivariate_feature.id,
        "string_value": "bigger",
    }

    # When
    response = admin_client.post(
        url, data=json.dumps(data), content_type="application/json"
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "default_percentage_allocation" in response.json()


def test_partial_update_mv_option__no_feature_or_percentage_allocation__keeps_them(
    admin_client: APIClient,
    project: Project,
    multivariate_feature: Feature,
) -> None:
    # Given
    option = multivariate_feature.multivariate_options.first()
    assert option is not None
    original_allocation = option.default_percentage_allocation
    url = reverse(
        "api-v1:projects:feature-mv-options-detail",
        args=[project.id, multivariate_feature.id, option.id],
    )

    # When
    response = admin_client.patch(
        url,
        data=json.dumps({"string_value": "updated"}),
        content_type="application/json",
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    option.refresh_from_db()
    assert option.string_value == "updated"
    assert option.default_percentage_allocation == original_allocation
