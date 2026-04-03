import pytest
import requests as _requests
import responses
from django.urls import reverse
from pytest_mock import MockerFixture
from rest_framework import status
from rest_framework.test import APIClient

from features.feature_external_resources.models import FeatureExternalResource
from features.models import Feature
from integrations.gitlab.models import GitLabConfiguration
from projects.models import Project

GITLAB_INSTANCE_URL = "https://gitlab.example.com"


def test_get_gitlab_configuration__no_configuration_exists__returns_200(
    admin_client_new: APIClient,
    project: Project,
) -> None:
    # Given
    url = reverse(
        "api-v1:projects:integrations-gitlab-list",
        kwargs={"project_pk": project.id},
    )

    # When
    response = admin_client_new.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK


def test_get_gitlab_configuration__existing_config__returns_list(
    admin_client_new: APIClient,
    project: Project,
    gitlab_configuration: GitLabConfiguration,
) -> None:
    # Given
    url = reverse(
        "api-v1:projects:integrations-gitlab-list",
        kwargs={"project_pk": project.id},
    )

    # When
    response = admin_client_new.get(url)
    response_json = response.json()

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert len(response_json["results"]) == 1
    assert response_json["results"][0]["id"] == gitlab_configuration.id
    assert "access_token" not in response_json["results"][0]


def test_create_gitlab_configuration__valid_data__returns_201(
    admin_client_new: APIClient,
    project: Project,
) -> None:
    # Given
    data = {
        "gitlab_instance_url": GITLAB_INSTANCE_URL,
        "access_token": "new-token",
        "webhook_secret": "new-secret",
    }
    url = reverse(
        "api-v1:projects:integrations-gitlab-list",
        kwargs={"project_pk": project.id},
    )

    # When
    response = admin_client_new.post(url, data)

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert GitLabConfiguration.objects.filter(project=project).exists()
    assert "access_token" not in response.json()


def test_create_gitlab_configuration__tagging_enabled__creates_label(
    admin_client_new: APIClient,
    project: Project,
    mocker: MockerFixture,
) -> None:
    # Given
    mock_create_label = mocker.patch(
        "integrations.gitlab.views.create_flagsmith_flag_label"
    )
    data = {
        "gitlab_instance_url": GITLAB_INSTANCE_URL,
        "access_token": "new-token",
        "webhook_secret": "new-secret",
        "tagging_enabled": True,
        "gitlab_project_id": 42,
    }
    url = reverse(
        "api-v1:projects:integrations-gitlab-list",
        kwargs={"project_pk": project.id},
    )

    # When
    response = admin_client_new.post(url, data, format="json")

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    mock_create_label.assert_called_once_with(
        instance_url=GITLAB_INSTANCE_URL,
        access_token="new-token",
        gitlab_project_id=42,
    )


def test_update_gitlab_configuration__tagging_enabled__creates_label(
    admin_client_new: APIClient,
    project: Project,
    gitlab_configuration: GitLabConfiguration,
    mocker: MockerFixture,
) -> None:
    # Given
    mock_create_label = mocker.patch(
        "integrations.gitlab.views.create_flagsmith_flag_label"
    )
    data = {
        "gitlab_instance_url": gitlab_configuration.gitlab_instance_url,
        "access_token": gitlab_configuration.access_token,
        "webhook_secret": gitlab_configuration.webhook_secret,
        "tagging_enabled": True,
        "gitlab_project_id": gitlab_configuration.gitlab_project_id,
    }
    url = reverse(
        "api-v1:projects:integrations-gitlab-detail",
        args=[project.id, gitlab_configuration.id],
    )

    # When
    response = admin_client_new.put(url, data, format="json")

    # Then
    assert response.status_code == status.HTTP_200_OK
    mock_create_label.assert_called_once_with(
        instance_url=gitlab_configuration.gitlab_instance_url,
        access_token=gitlab_configuration.access_token,
        gitlab_project_id=gitlab_configuration.gitlab_project_id,
    )


def test_delete_gitlab_configuration__valid_configuration__returns_204(
    admin_client_new: APIClient,
    project: Project,
    gitlab_configuration: GitLabConfiguration,
) -> None:
    # Given
    url = reverse(
        "api-v1:projects:integrations-gitlab-detail",
        args=[project.id, gitlab_configuration.id],
    )

    # When
    response = admin_client_new.delete(url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not GitLabConfiguration.objects.filter(id=gitlab_configuration.id).exists()


def test_delete_gitlab_configuration__has_external_resources__removes_them(
    admin_client_new: APIClient,
    project: Project,
    gitlab_configuration: GitLabConfiguration,
    feature: Feature,
    mocker: MockerFixture,
) -> None:
    # Given
    FeatureExternalResource.objects.create(
        url="https://gitlab.example.com/testgroup/testrepo/-/issues/1",
        type="GITLAB_ISSUE",
        feature=feature,
        metadata='{"state": "opened"}',
    )
    url = reverse(
        "api-v1:projects:integrations-gitlab-detail",
        args=[project.id, gitlab_configuration.id],
    )
    assert FeatureExternalResource.objects.filter(feature=feature).exists()

    # When
    response = admin_client_new.delete(url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not FeatureExternalResource.objects.filter(
        feature=feature, type="GITLAB_ISSUE"
    ).exists()


def test_gitlab_configuration__non_existent_project__returns_403(
    admin_client_new: APIClient,
) -> None:
    # Given
    url = reverse(
        "api-v1:projects:integrations-gitlab-list",
        kwargs={"project_pk": 999999},
    )

    # When
    response = admin_client_new.get(url)

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


@responses.activate
def test_fetch_projects__valid_request__returns_projects(
    admin_client_new: APIClient,
    project: Project,
    gitlab_configuration: GitLabConfiguration,
) -> None:
    # Given
    responses.add(
        method="GET",
        url=f"{GITLAB_INSTANCE_URL}/api/v4/projects",
        status=200,
        json=[
            {
                "id": 1,
                "name": "My Project",
                "path_with_namespace": "testgroup/myproject",
            }
        ],
        headers={"x-page": "1", "x-total-pages": "1", "x-total": "1"},
    )
    url = reverse("api-v1:projects:get-gitlab-projects", args=[project.id])

    # When
    response = admin_client_new.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 1
    assert response.json()["results"][0]["name"] == "My Project"


@responses.activate
def test_fetch_issues__valid_request__returns_results(
    admin_client_new: APIClient,
    project: Project,
    gitlab_configuration: GitLabConfiguration,
) -> None:
    # Given
    responses.add(
        method="GET",
        url=f"{GITLAB_INSTANCE_URL}/api/v4/projects/1/issues",
        status=200,
        json=[
            {
                "web_url": f"{GITLAB_INSTANCE_URL}/testgroup/testrepo/-/issues/1",
                "id": 101,
                "title": "Test Issue",
                "iid": 1,
                "state": "opened",
            }
        ],
        headers={"x-page": "1", "x-total-pages": "1", "x-total": "1"},
    )
    url = reverse("api-v1:projects:get-gitlab-issues", args=[project.id])

    # When
    response = admin_client_new.get(url, data={"gitlab_project_id": 1})

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 1
    assert response.json()["results"][0]["title"] == "Test Issue"


@responses.activate
def test_fetch_merge_requests__valid_request__returns_results(
    admin_client_new: APIClient,
    project: Project,
    gitlab_configuration: GitLabConfiguration,
) -> None:
    # Given
    responses.add(
        method="GET",
        url=f"{GITLAB_INSTANCE_URL}/api/v4/projects/1/merge_requests",
        status=200,
        json=[
            {
                "web_url": f"{GITLAB_INSTANCE_URL}/testgroup/testrepo/-/merge_requests/1",
                "id": 201,
                "title": "Test MR",
                "iid": 1,
                "state": "opened",
                "draft": False,
                "merged_at": None,
            }
        ],
        headers={"x-page": "1", "x-total-pages": "1", "x-total": "1"},
    )
    url = reverse("api-v1:projects:get-gitlab-merge-requests", args=[project.id])

    # When
    response = admin_client_new.get(url, data={"gitlab_project_id": 1})

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 1
    assert response.json()["results"][0]["title"] == "Test MR"
    assert response.json()["results"][0]["merged"] is False


@responses.activate
def test_fetch_project_members__valid_request__returns_members(
    admin_client_new: APIClient,
    project: Project,
    gitlab_configuration: GitLabConfiguration,
) -> None:
    # Given
    responses.add(
        method="GET",
        url=f"{GITLAB_INSTANCE_URL}/api/v4/projects/1/members",
        status=200,
        json=[
            {
                "username": "jdoe",
                "avatar_url": f"{GITLAB_INSTANCE_URL}/avatar/jdoe",
                "name": "John Doe",
            }
        ],
        headers={"x-page": "1", "x-total-pages": "1"},
    )
    url = reverse("api-v1:projects:get-gitlab-project-members", args=[project.id])

    # When
    response = admin_client_new.get(url, data={"gitlab_project_id": 1})

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["results"][0]["username"] == "jdoe"


def test_fetch_issues__missing_config__returns_400(
    admin_client_new: APIClient,
    project: Project,
) -> None:
    # Given
    url = reverse("api-v1:projects:get-gitlab-issues", args=[project.id])

    # When
    response = admin_client_new.get(url, data={"gitlab_project_id": 1})

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "doesn't have a valid GitLab configuration" in response.json()["detail"]


def test_fetch_merge_requests__missing_config__returns_400(
    admin_client_new: APIClient,
    project: Project,
) -> None:
    # Given
    url = reverse("api-v1:projects:get-gitlab-merge-requests", args=[project.id])

    # When
    response = admin_client_new.get(url, data={"gitlab_project_id": 1})

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "doesn't have a valid GitLab configuration" in response.json()["detail"]


@pytest.mark.parametrize(
    "url_name",
    [
        "get-gitlab-merge-requests",
        "get-gitlab-issues",
        "get-gitlab-projects",
        "get-gitlab-project-members",
    ],
)
def test_fetch_resource__invalid_query_params__returns_400(
    admin_client_new: APIClient,
    project: Project,
    gitlab_configuration: GitLabConfiguration,
    url_name: str,
) -> None:
    # Given
    url = reverse(f"api-v1:projects:{url_name}", args=[project.id])

    # When
    response = admin_client_new.get(url, data={"gitlab_project_id": "1", "page": "abc"})

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "error" in response.json()


def test_gitlab_api_call_error_handler__value_error__returns_400(
    admin_client_new: APIClient,
    project: Project,
    gitlab_configuration: GitLabConfiguration,
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch(
        "integrations.gitlab.views.fetch_search_gitlab_resource",
        side_effect=ValueError("bad value"),
    )
    url = reverse("api-v1:projects:get-gitlab-issues", args=[project.id])

    # When
    response = admin_client_new.get(url, data={"gitlab_project_id": 1})

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Failed to retrieve GitLab issues" in response.json()["detail"]
    assert "bad value" in response.json()["detail"]


def test_gitlab_api_call_error_handler__request_exception__returns_502(
    admin_client_new: APIClient,
    project: Project,
    gitlab_configuration: GitLabConfiguration,
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch(
        "integrations.gitlab.views.fetch_search_gitlab_resource",
        side_effect=_requests.RequestException("connection failed"),
    )
    url = reverse("api-v1:projects:get-gitlab-issues", args=[project.id])

    # When
    response = admin_client_new.get(url, data={"gitlab_project_id": 1})

    # Then
    assert response.status_code == status.HTTP_502_BAD_GATEWAY
    assert "Failed to retrieve GitLab issues" in response.json()["detail"]
    assert "connection failed" in response.json()["detail"]
