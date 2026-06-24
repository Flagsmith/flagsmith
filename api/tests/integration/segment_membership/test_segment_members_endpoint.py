import pytest
from common.environments.permissions import VIEW_IDENTITIES
from common.projects.permissions import MANAGE_SEGMENTS, VIEW_PROJECT
from rest_framework import status
from rest_framework.test import APIClient

from organisations.models import Organisation
from tests.types import (
    EnableFeaturesFixture,
    WithEnvironmentPermissionsCallable,
    WithProjectPermissionsCallable,
)
from users.models import FFAdminUser


def test_get_segment_members__flag_off__returns_404(
    admin_client: APIClient,
    project: int,
    environment: int,
    segment: int,
) -> None:
    # Given
    # the org's segment_membership_inspection flag is off (default)

    # When
    response = admin_client.get(
        f"/api/v1/projects/{project}/segments/{segment}/members/?environment={environment}"
    )

    # Then
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_segment_members__limit_exceeds_max__returns_400(
    admin_client: APIClient,
    project: int,
    environment: int,
    segment: int,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features("segment_membership_inspection")

    # When
    # a page size above the cap is requested
    response = admin_client.get(
        f"/api/v1/projects/{project}/segments/{segment}/members/?environment={environment}&limit=201"
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_get_segment_members__missing_view_identities__returns_403(
    staff_user: FFAdminUser,
    staff_client: APIClient,
    organisation: int,
    project: int,
    environment: int,
    segment: int,
    enable_features: EnableFeaturesFixture,
    with_project_permissions: WithProjectPermissionsCallable,
) -> None:
    # Given
    enable_features("segment_membership_inspection")
    # a user with MANAGE_SEGMENTS on the project but no VIEW_IDENTITIES
    # on the environment
    staff_user.add_organisation(Organisation.objects.get(id=organisation))
    with_project_permissions([MANAGE_SEGMENTS, VIEW_PROJECT], project, False)

    # When
    response = staff_client.get(
        f"/api/v1/projects/{project}/segments/{segment}/members/?environment={environment}"
    )

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.clickhouse
def test_get_segment_members__has_both_permissions__returns_200(
    clickhouse_db: None,
    staff_user: FFAdminUser,
    staff_client: APIClient,
    organisation: int,
    project: int,
    environment: int,
    segment: int,
    enable_features: EnableFeaturesFixture,
    with_project_permissions: WithProjectPermissionsCallable,
    with_environment_permissions: WithEnvironmentPermissionsCallable,
) -> None:
    # Given
    enable_features("segment_membership_inspection")
    staff_user.add_organisation(Organisation.objects.get(id=organisation))
    with_project_permissions([MANAGE_SEGMENTS, VIEW_PROJECT], project, False)
    with_environment_permissions([VIEW_IDENTITIES], environment, False)

    # When
    response = staff_client.get(
        f"/api/v1/projects/{project}/segments/{segment}/members/?environment={environment}"
    )

    # Then the RBAC gate (MANAGE_SEGMENTS + VIEW_IDENTITIES) is satisfied
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"results": [], "next_cursor": None}


@pytest.mark.clickhouse
def test_get_segment_members__matching_identities__returns_members(
    segment_membership_identities: None,
    admin_client: APIClient,
    project: int,
    environment: int,
    segment: int,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features("segment_membership_inspection")

    # When
    response = admin_client.get(
        f"/api/v1/projects/{project}/segments/{segment}/members/?environment={environment}&limit=100"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "results": [
            {
                "identifier": "alice",
                "identity_key": "alice_key",
                "traits": {"foo": "bar"},
            },
            {"identifier": "bob", "identity_key": "bob_key", "traits": {"foo": "bar"}},
        ],
        "next_cursor": None,
    }


@pytest.mark.clickhouse
def test_get_segment_members__q__filters_by_identifier(
    segment_membership_identities: None,
    admin_client: APIClient,
    project: int,
    environment: int,
    segment: int,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given
    enable_features("segment_membership_inspection")

    # When
    response = admin_client.get(
        f"/api/v1/projects/{project}/segments/{segment}/members/?environment={environment}&q=ali"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "results": [
            {
                "identifier": "alice",
                "identity_key": "alice_key",
                "traits": {"foo": "bar"},
            },
        ],
        "next_cursor": None,
    }


@pytest.mark.clickhouse
def test_get_segment_members__more_results_than_limit__returns_next_cursor(
    segment_membership_identities: None,
    admin_client: APIClient,
    project: int,
    environment: int,
    segment: int,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given two matching identities (alice, bob)
    enable_features("segment_membership_inspection")

    # When a page smaller than the match count is requested
    response = admin_client.get(
        f"/api/v1/projects/{project}/segments/{segment}/members/?environment={environment}&limit=1"
    )

    # Then there's a further page, so next_cursor is the last identifier
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "results": [
            {
                "identifier": "alice",
                "identity_key": "alice_key",
                "traits": {"foo": "bar"},
            },
        ],
        "next_cursor": "alice",
    }


@pytest.mark.clickhouse
def test_get_segment_members__limit_equals_match_count__no_next_cursor(
    segment_membership_identities: None,
    admin_client: APIClient,
    project: int,
    environment: int,
    segment: int,
    enable_features: EnableFeaturesFixture,
) -> None:
    # Given two matching identities and a limit of exactly two
    enable_features("segment_membership_inspection")

    # When
    response = admin_client.get(
        f"/api/v1/projects/{project}/segments/{segment}/members/?environment={environment}&limit=2"
    )

    # Then there's no further page -- next_cursor is null rather than advertising
    # a phantom empty page at the exact boundary
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "results": [
            {
                "identifier": "alice",
                "identity_key": "alice_key",
                "traits": {"foo": "bar"},
            },
            {"identifier": "bob", "identity_key": "bob_key", "traits": {"foo": "bar"}},
        ],
        "next_cursor": None,
    }
