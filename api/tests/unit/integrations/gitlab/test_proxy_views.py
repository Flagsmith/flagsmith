from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
import requests
from rest_framework import status

from integrations.gitlab.models import GitLabConfiguration

if TYPE_CHECKING:
    from pytest_mock import MockerFixture
    from rest_framework.test import APIClient

    from projects.models import Project


@pytest.fixture()
def gitlab_config(project: Project) -> GitLabConfiguration:
    return GitLabConfiguration.objects.create(  # type: ignore[no-any-return]
        project=project,
        gitlab_instance_url="https://gitlab.example.com",
        access_token="glpat-test-token",
    )


@pytest.mark.usefixtures("gitlab_config")
def test_gitlab_project_list__valid_config__returns_paginated_response(
    admin_client: APIClient,
    project: Project,
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch(
        "integrations.gitlab.views.browse_gitlab.fetch_gitlab_projects",
        return_value={
            "results": [{"id": 1, "name": "P", "path_with_namespace": "g/p"}],
            "current_page": 1,
            "total_pages": 2,
            "total_count": 150,
        },
    )

    # When
    response = admin_client.get(
        f"/api/v1/projects/{project.id}/gitlab/projects/",
        {"page": 1, "page_size": 100},
    )

    # Then
    data = response.json()
    assert response.status_code == status.HTTP_200_OK
    assert data["results"][0]["name"] == "P"
    assert data["count"] == 150
    assert data["next"] is not None
    assert data["previous"] is None


def test_gitlab_project_list__no_gitlab_config__returns_400(
    admin_client: APIClient,
    project: Project,
) -> None:
    # Given / When
    response = admin_client.get(
        f"/api/v1/projects/{project.id}/gitlab/projects/",
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.usefixtures("gitlab_config")
def test_gitlab_issue_list__valid_config__returns_issues(
    admin_client: APIClient,
    project: Project,
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch(
        "integrations.gitlab.views.browse_gitlab.search_gitlab_issues",
        return_value={
            "results": [
                {
                    "web_url": "https://gitlab.example.com/g/p/-/issues/1",
                    "id": 101,
                    "title": "Bug",
                    "iid": 1,
                    "state": "opened",
                }
            ],
            "current_page": 1,
            "total_pages": 1,
            "total_count": 1,
        },
    )

    # When
    response = admin_client.get(
        f"/api/v1/projects/{project.id}/gitlab/issues/",
        {"gitlab_project_id": 42},
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["results"][0]["title"] == "Bug"


@pytest.mark.usefixtures("gitlab_config")
def test_gitlab_issue_list__missing_gitlab_project_id__returns_400(
    admin_client: APIClient,
    project: Project,
) -> None:
    # Given / When
    response = admin_client.get(
        f"/api/v1/projects/{project.id}/gitlab/issues/",
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.usefixtures("gitlab_config")
def test_gitlab_merge_request_list__valid_config__returns_merge_requests(
    admin_client: APIClient,
    project: Project,
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch(
        "integrations.gitlab.views.browse_gitlab.search_gitlab_merge_requests",
        return_value={
            "results": [
                {
                    "web_url": "https://gitlab.example.com/g/p/-/merge_requests/5",
                    "id": 201,
                    "title": "Feature",
                    "iid": 5,
                    "state": "opened",
                    "merged": False,
                    "draft": False,
                }
            ],
            "current_page": 1,
            "total_pages": 1,
            "total_count": 1,
        },
    )

    # When
    response = admin_client.get(
        f"/api/v1/projects/{project.id}/gitlab/merge-requests/",
        {"gitlab_project_id": 42},
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["results"][0]["title"] == "Feature"


def test_gitlab_merge_request_list__no_gitlab_config__returns_400(
    admin_client: APIClient,
    project: Project,
) -> None:
    # Given / When
    response = admin_client.get(
        f"/api/v1/projects/{project.id}/gitlab/merge-requests/",
        {"gitlab_project_id": 42},
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.usefixtures("gitlab_config")
def test_gitlab_merge_request_list__missing_gitlab_project_id__returns_400(
    admin_client: APIClient,
    project: Project,
) -> None:
    # Given / When
    response = admin_client.get(
        f"/api/v1/projects/{project.id}/gitlab/merge-requests/",
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.usefixtures("gitlab_config")
def test_browse_gitlab__api_unreachable__returns_503(
    admin_client: APIClient,
    project: Project,
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch(
        "integrations.gitlab.views.browse_gitlab.fetch_gitlab_projects",
        side_effect=requests.RequestException("connection refused"),
    )

    # When
    response = admin_client.get(
        f"/api/v1/projects/{project.id}/gitlab/projects/",
    )

    # Then
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.json()["detail"] == "GitLab API is unreachable"
