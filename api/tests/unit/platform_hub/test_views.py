import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from environments.models import Environment
from features.models import Feature
from organisations.models import Organisation, OrganisationRole
from projects.models import Project
from users.models import FFAdminUser


def test_summary_view__unauthenticated__returns_401(db: None) -> None:
    # Given
    client = APIClient()
    url = reverse("api-v1:platform-hub:summary")

    # When
    response = client.get(url)

    # Then
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_summary_view__user_admin_of_one_org__returns_counts_for_that_org_only(
    platform_hub_admin_client: APIClient,
    platform_hub_organisation: Organisation,
    platform_hub_project: Project,
    platform_hub_environment: Environment,
    platform_hub_feature: Feature,
    other_organisation: Organisation,
    other_org_project: Project,
    other_org_environment: Environment,
    other_org_feature: Feature,
) -> None:
    # Given
    url = reverse("api-v1:platform-hub:summary")

    # When
    response = platform_hub_admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total_organisations"] == 1
    assert data["total_projects"] == 1
    assert data["total_environments"] == 1
    assert data["total_flags"] == 1
    assert data["total_users"] == 1


def test_summary_view__user_admin_of_multiple_orgs__returns_aggregated_counts(
    platform_hub_admin_client: APIClient,
    platform_hub_admin_user: FFAdminUser,
    platform_hub_organisation: Organisation,
    platform_hub_project: Project,
    platform_hub_environment: Environment,
    platform_hub_feature: Feature,
    other_organisation: Organisation,
    other_org_project: Project,
    other_org_environment: Environment,
    other_org_feature: Feature,
) -> None:
    # Given
    platform_hub_admin_user.add_organisation(
        other_organisation, role=OrganisationRole.ADMIN
    )
    url = reverse("api-v1:platform-hub:summary")

    # When
    response = platform_hub_admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total_organisations"] == 2
    assert data["total_projects"] == 2
    assert data["total_environments"] == 2
    assert data["total_flags"] == 2


def test_summary_view__user_not_admin_of_any_org__returns_zero_counts(
    db: None,
) -> None:
    # Given
    user: FFAdminUser = FFAdminUser.objects.create_user(  # type: ignore[no-untyped-call]
        email="nonadmin@test.com",
        password="testpass123!",
    )
    client = APIClient()
    client.force_authenticate(user=user)
    url = reverse("api-v1:platform-hub:summary")

    # When
    response = client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total_organisations"] == 0
    assert data["total_flags"] == 0
    assert data["total_users"] == 0
    assert data["total_projects"] == 0
    assert data["total_environments"] == 0


def test_summary_view__invalid_days__returns_400(
    platform_hub_admin_client: APIClient,
    platform_hub_organisation: Organisation,
) -> None:
    # Given
    url = reverse("api-v1:platform-hub:summary")

    # When
    response = platform_hub_admin_client.get(url, {"days": 45})

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_organisations_view__user_admin_of_one_org__returns_only_that_org(
    platform_hub_admin_client: APIClient,
    platform_hub_organisation: Organisation,
    platform_hub_project: Project,
    platform_hub_environment: Environment,
    platform_hub_feature: Feature,
    other_organisation: Organisation,
    other_org_project: Project,
    other_org_environment: Environment,
    other_org_feature: Feature,
) -> None:
    # Given
    url = reverse("api-v1:platform-hub:organisations")

    # When
    response = platform_hub_admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == platform_hub_organisation.id
    assert data[0]["name"] == "Platform Hub Org"


def test_organisations_view__other_orgs_data_not_visible(
    platform_hub_admin_client: APIClient,
    platform_hub_organisation: Organisation,
    other_organisation: Organisation,
    other_org_project: Project,
    other_org_environment: Environment,
    other_org_feature: Feature,
) -> None:
    # Given
    url = reverse("api-v1:platform-hub:organisations")

    # When
    response = platform_hub_admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    org_ids = [org["id"] for org in data]
    assert other_organisation.id not in org_ids


def test_organisations_view__returns_nested_projects_and_environments(
    platform_hub_admin_client: APIClient,
    platform_hub_organisation: Organisation,
    platform_hub_project: Project,
    platform_hub_environment: Environment,
    platform_hub_feature: Feature,
) -> None:
    # Given
    url = reverse("api-v1:platform-hub:organisations")

    # When
    response = platform_hub_admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    org = data[0]
    assert len(org["projects"]) == 1
    assert org["projects"][0]["name"] == "Hub Project"
    assert len(org["projects"][0]["environments"]) == 1
    assert org["projects"][0]["environments"][0]["name"] == "Hub Environment"


def test_organisations_view__includes_overage_fields(
    platform_hub_admin_client: APIClient,
    platform_hub_organisation: Organisation,
    platform_hub_project: Project,
    platform_hub_environment: Environment,
) -> None:
    # Given
    url = reverse("api-v1:platform-hub:organisations")

    # When
    response = platform_hub_admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    org = data[0]
    assert "overage_30d" in org
    assert "overage_60d" in org
    assert "overage_90d" in org
    assert "api_calls_allowed" in org


def test_usage_trends_view__returns_trends_for_admin_orgs_only(
    platform_hub_admin_client: APIClient,
    platform_hub_organisation: Organisation,
) -> None:
    # Given
    url = reverse("api-v1:platform-hub:usage-trends")

    # When
    response = platform_hub_admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)


def test_stale_flags_view__returns_stale_flags_for_admin_orgs_only(
    platform_hub_admin_client: APIClient,
    platform_hub_organisation: Organisation,
    platform_hub_project: Project,
    platform_hub_environment: Environment,
    platform_hub_feature: Feature,
    other_organisation: Organisation,
    other_org_project: Project,
    other_org_environment: Environment,
    other_org_feature: Feature,
) -> None:
    # Given
    url = reverse("api-v1:platform-hub:stale-flags")

    # When
    response = platform_hub_admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    org_ids = [item["organisation_id"] for item in data]
    assert other_organisation.id not in org_ids


def test_integrations_view__returns_integrations_for_admin_orgs_only(
    platform_hub_admin_client: APIClient,
    platform_hub_organisation: Organisation,
    other_organisation: Organisation,
) -> None:
    # Given
    url = reverse("api-v1:platform-hub:integrations")

    # When
    response = platform_hub_admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    for item in data:
        assert item["organisation_id"] != other_organisation.id


def test_release_pipelines_view__returns_pipelines_for_admin_orgs_only(
    platform_hub_admin_client: APIClient,
    platform_hub_organisation: Organisation,
) -> None:
    # Given
    url = reverse("api-v1:platform-hub:release-pipelines")

    # When
    response = platform_hub_admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)


def test_release_pipelines_view__pipelines_not_installed__returns_empty_list(
    platform_hub_admin_client: APIClient,
    platform_hub_organisation: Organisation,
    settings: pytest.FixtureRequest,
) -> None:
    # Given
    settings.RELEASE_PIPELINES_LOGIC_INSTALLED = False  # type: ignore[attr-defined]
    url = reverse("api-v1:platform-hub:release-pipelines")

    # When
    response = platform_hub_admin_client.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []
