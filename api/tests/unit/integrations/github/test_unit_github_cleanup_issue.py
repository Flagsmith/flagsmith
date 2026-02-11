import json
from datetime import datetime
from typing import Any

import pytest
import responses
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture
from rest_framework import status
from rest_framework.test import APIClient

from features.feature_external_resources.models import FeatureExternalResource
from features.models import Feature
from integrations.github.constants import GITHUB_API_URL
from organisations.models import Organisation
from projects.code_references.types import (
    CodeReference,
    FeatureFlagCodeReferencesRepositorySummary,
    VCSProvider,
)
from users.models import FFAdminUser

REPOSITORY_URL_1 = "https://github.com/myorg/myrepo"
REPOSITORY_URL_2 = "https://github.com/myorg/other-repo"


@pytest.fixture()
def set_github_pat(settings: SettingsWrapper) -> None:
    settings.FEATURE_LIFECYCLE_GITHUB_PAT = "test-pat"


@pytest.fixture()
def mock_code_references(
    feature: Feature,
    mocker: MockerFixture,
) -> None:
    mocker.patch(
        "integrations.github.views.get_code_references_for_feature_flag",
        return_value=[
            FeatureFlagCodeReferencesRepositorySummary(
                repository_url=REPOSITORY_URL_1,
                vcs_provider=VCSProvider.GITHUB,
                revision="abc123",
                last_successful_repository_scanned_at=datetime(2025, 1, 1),
                last_feature_found_at=datetime(2025, 1, 1),
                code_references=[
                    CodeReference(
                        feature_name=feature.name,
                        file_path="src/app.py",
                        line_number=42,
                        permalink=f"{REPOSITORY_URL_1}/blob/abc123/src/app.py#L42",
                    ),
                ],
            ),
            FeatureFlagCodeReferencesRepositorySummary(
                repository_url=REPOSITORY_URL_2,
                vcs_provider=VCSProvider.GITHUB,
                revision="def456",
                last_successful_repository_scanned_at=datetime(2025, 1, 1),
                last_feature_found_at=datetime(2025, 1, 1),
                code_references=[
                    CodeReference(
                        feature_name=feature.name,
                        file_path="lib/flags.py",
                        line_number=7,
                        permalink=f"{REPOSITORY_URL_2}/blob/def456/lib/flags.py#L7",
                    ),
                ],
            ),
        ],
    )


@responses.activate
@pytest.mark.usefixtures("set_github_pat", "mock_code_references")
def test_create_cleanup_issue__valid_request__returns_204(
    admin_client_new: APIClient,
    organisation: Organisation,
    feature: Feature,
) -> None:
    # Given
    github_issue_response_1: dict[str, Any] = {
        "html_url": f"{REPOSITORY_URL_1}/issues/42",
        "id": 123456,
        "title": f"Remove stale feature flag: {feature.name}",
        "number": 42,
        "state": "open",
    }
    github_issue_response_2: dict[str, Any] = {
        "html_url": f"{REPOSITORY_URL_2}/issues/10",
        "id": 789012,
        "title": f"Remove stale feature flag: {feature.name}",
        "number": 10,
        "state": "open",
    }
    responses.add(
        method="POST",
        url=f"{GITHUB_API_URL}repos/myorg/myrepo/issues",
        status=201,
        json=github_issue_response_1,
    )
    responses.add(
        method="POST",
        url=f"{GITHUB_API_URL}repos/myorg/other-repo/issues",
        status=201,
        json=github_issue_response_2,
    )

    url = f"/api/v1/organisations/{organisation.id}/github/create-cleanup-issue/"

    # When
    response = admin_client_new.post(
        url,
        data={"feature_id": feature.id},
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert (
        FeatureExternalResource.objects.filter(
            feature=feature,
            type="GITHUB_ISSUE",
        ).count()
        == 2
    )

    assert len(responses.calls) == 2
    assert not isinstance(responses.calls[0], list)
    assert not isinstance(responses.calls[1], list)
    request_body_1 = json.loads(responses.calls[0].request.body)
    assert request_body_1["title"] == f"Remove stale feature flag: {feature.name}"
    assert "src/app.py#L42" in request_body_1["body"]
    request_body_2 = json.loads(responses.calls[1].request.body)
    assert "lib/flags.py#L7" in request_body_2["body"]


@responses.activate
@pytest.mark.usefixtures("set_github_pat", "mock_code_references")
def test_create_cleanup_issue__duplicate_link__skips_silently(
    admin_client_new: APIClient,
    organisation: Organisation,
    feature: Feature,
) -> None:
    # Given
    github_issue_response: dict[str, Any] = {
        "html_url": f"{REPOSITORY_URL_1}/issues/42",
        "id": 123456,
        "title": f"Remove stale feature flag: {feature.name}",
        "number": 42,
        "state": "open",
    }
    responses.add(
        method="POST",
        url=f"{GITHUB_API_URL}repos/myorg/myrepo/issues",
        status=201,
        json=github_issue_response,
    )
    responses.add(
        method="POST",
        url=f"{GITHUB_API_URL}repos/myorg/other-repo/issues",
        status=201,
        json={
            "html_url": f"{REPOSITORY_URL_2}/issues/10",
            "id": 789012,
            "title": f"Remove stale feature flag: {feature.name}",
            "number": 10,
            "state": "open",
        },
    )
    FeatureExternalResource.objects.create(
        url=github_issue_response["html_url"],
        type="GITHUB_ISSUE",
        feature=feature,
    )

    url = f"/api/v1/organisations/{organisation.id}/github/create-cleanup-issue/"

    # When
    response = admin_client_new.post(
        url,
        data={"feature_id": feature.id},
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_create_cleanup_issue__pat_not_configured__returns_400(
    admin_client_new: APIClient,
    organisation: Organisation,
    feature: Feature,
    settings: SettingsWrapper,
) -> None:
    # Given
    settings.FEATURE_LIFECYCLE_GITHUB_PAT = ""

    url = f"/api/v1/organisations/{organisation.id}/github/create-cleanup-issue/"

    # When
    response = admin_client_new.post(
        url,
        data={"feature_id": feature.id},
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "GitHub PAT is not configured" in response.json()["detail"]


@pytest.mark.usefixtures("set_github_pat")
def test_create_cleanup_issue__feature_not_found__returns_404(
    admin_client_new: APIClient,
    organisation: Organisation,
) -> None:
    # Given
    url = f"/api/v1/organisations/{organisation.id}/github/create-cleanup-issue/"

    # When
    response = admin_client_new.post(
        url,
        data={"feature_id": 999999},
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Feature not found" in response.json()["detail"]


@pytest.mark.usefixtures("set_github_pat")
def test_create_cleanup_issue__missing_fields__returns_400(
    admin_client_new: APIClient,
    organisation: Organisation,
) -> None:
    # Given
    url = f"/api/v1/organisations/{organisation.id}/github/create-cleanup-issue/"

    # When
    response = admin_client_new.post(url, data={}, format="json")

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.usefixtures("set_github_pat")
def test_create_cleanup_issue__no_code_references__returns_400(
    admin_client_new: APIClient,
    organisation: Organisation,
    feature: Feature,
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch(
        "integrations.github.views.get_code_references_for_feature_flag",
        return_value=[],
    )

    url = f"/api/v1/organisations/{organisation.id}/github/create-cleanup-issue/"

    # When
    response = admin_client_new.post(
        url,
        data={"feature_id": feature.id},
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "No code references found" in response.json()["detail"]


@responses.activate
@pytest.mark.usefixtures("set_github_pat", "mock_code_references")
def test_create_cleanup_issue__github_api_error__returns_502(
    admin_client_new: APIClient,
    organisation: Organisation,
    feature: Feature,
) -> None:
    # Given
    responses.add(
        method="POST",
        url=f"{GITHUB_API_URL}repos/myorg/myrepo/issues",
        status=500,
        json={"message": "Internal Server Error"},
    )

    url = f"/api/v1/organisations/{organisation.id}/github/create-cleanup-issue/"

    # When
    response = admin_client_new.post(
        url,
        data={"feature_id": feature.id},
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_502_BAD_GATEWAY
    assert "Failed to create GitHub cleanup issue" in response.json()["detail"]


def test_create_cleanup_issue__user_not_in_org__returns_403(
    api_client: APIClient,
    organisation: Organisation,
    feature: Feature,
) -> None:
    # Given
    user = FFAdminUser.objects.create(email="outsider@example.com")
    api_client.force_authenticate(user)

    url = f"/api/v1/organisations/{organisation.id}/github/create-cleanup-issue/"

    # When
    response = api_client.post(
        url,
        data={"feature_id": feature.id},
        format="json",
    )

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN
