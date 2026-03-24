import json
from unittest.mock import MagicMock

import pytest
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

WEBHOOK_MR_PAYLOAD = json.dumps(
    {
        "object_kind": "merge_request",
        "event_type": "merge_request",
        "project": {
            "path_with_namespace": "testgroup/testrepo",
        },
        "object_attributes": {
            "action": "open",
            "url": "https://gitlab.example.com/testgroup/testrepo/-/merge_requests/1",
            "state": "opened",
            "work_in_progress": False,
        },
    }
)


# ---------------------------------------------------------------
# Configuration tests
# ---------------------------------------------------------------


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
    assert GitLabConfiguration.objects.filter(
        project=project
    ).exists()


def test_create_gitlab_configuration__duplicate__returns_400(
    admin_client_new: APIClient,
    project: Project,
    gitlab_configuration: GitLabConfiguration,
) -> None:
    # Given
    data = {
        "gitlab_instance_url": "https://gitlab.other.com",
        "access_token": "another-token",
        "webhook_secret": "another-secret",
    }
    url = reverse(
        "api-v1:projects:integrations-gitlab-list",
        kwargs={"project_pk": project.id},
    )
    # When
    response = admin_client_new.post(url, data)
    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert (
        "Duplication error. The GitLab integration already created"
        in response.json()["detail"]
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
    assert not GitLabConfiguration.objects.filter(
        id=gitlab_configuration.id
    ).exists()


@responses.activate
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


@responses.activate
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


def test_delete_gitlab_configuration__has_external_resources__removes_them(
    admin_client_new: APIClient,
    project: Project,
    gitlab_configuration: GitLabConfiguration,
    feature: Feature,
    post_request_mock: MagicMock,
    mock_github_client_generate_token: MagicMock,
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch(
        "features.feature_external_resources.models.FeatureExternalResource._handle_gitlab_after_save"
    )

    FeatureExternalResource.objects.create(
        url="https://gitlab.example.com/testgroup/testrepo/-/issues/1",
        type="GITLAB_ISSUE",
        feature=feature,
        metadata='{"state": "opened"}',
    )

    url = reverse(
        "api-v1:projects:integrations-gitlab-detail",
        args=[
            project.id,
            gitlab_configuration.id,
        ],
    )
    assert FeatureExternalResource.objects.filter(feature=feature).exists()

    # When
    response = admin_client_new.delete(url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not FeatureExternalResource.objects.filter(
        feature=feature, type="GITLAB_ISSUE"
    ).exists()


# ---------------------------------------------------------------
# Webhook tests
# ---------------------------------------------------------------


@pytest.mark.django_db
def test_gitlab_webhook__valid_merge_request_event__returns_200(
    project: Project,
    gitlab_configuration: GitLabConfiguration,
) -> None:
    # Given
    client = APIClient()
    url = reverse("api-v1:gitlab-webhook", args=[project.id])

    # When
    response = client.post(
        url,
        data=WEBHOOK_MR_PAYLOAD,
        content_type="application/json",
        **{  # type: ignore[arg-type]
            "HTTP_X_GITLAB_TOKEN": gitlab_configuration.webhook_secret,
            "HTTP_X_GITLAB_EVENT": "Merge Request Hook",
        },
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["detail"] == "Event processed"


@pytest.mark.django_db
def test_gitlab_webhook__invalid_token__returns_400(
    project: Project,
    gitlab_configuration: GitLabConfiguration,
) -> None:
    # Given
    client = APIClient()
    url = reverse("api-v1:gitlab-webhook", args=[project.id])

    # When
    response = client.post(
        url,
        data=WEBHOOK_MR_PAYLOAD,
        content_type="application/json",
        **{  # type: ignore[arg-type]
            "HTTP_X_GITLAB_TOKEN": "wrong-secret",
            "HTTP_X_GITLAB_EVENT": "Merge Request Hook",
        },
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "Invalid token"


@pytest.mark.django_db
def test_gitlab_webhook__missing_token_header__returns_400(
    project: Project,
    gitlab_configuration: GitLabConfiguration,
) -> None:
    # Given
    client = APIClient()
    url = reverse("api-v1:gitlab-webhook", args=[project.id])

    # When
    response = client.post(
        url,
        data=WEBHOOK_MR_PAYLOAD,
        content_type="application/json",
        **{  # type: ignore[arg-type]
            "HTTP_X_GITLAB_EVENT": "Merge Request Hook",
        },
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["error"] == "Invalid token"


# ---------------------------------------------------------------
# Resource browsing tests
# ---------------------------------------------------------------


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

    url = reverse(
        "api-v1:projects:get-gitlab-projects",
        args=[project.id],
    )

    # When
    response = admin_client_new.get(url)
    response_json = response.json()

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert "results" in response_json
    assert len(response_json["results"]) == 1
    assert response_json["results"][0]["name"] == "My Project"


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
                "web_url": "https://gitlab.example.com/testgroup/testrepo/-/issues/1",
                "id": 101,
                "title": "Test Issue",
                "iid": 1,
                "state": "opened",
            }
        ],
        headers={"x-page": "1", "x-total-pages": "1", "x-total": "1"},
    )

    url = reverse(
        "api-v1:projects:get-gitlab-issues",
        args=[project.id],
    )
    data = {"gitlab_project_id": 1}

    # When
    response = admin_client_new.get(url, data=data)
    response_json = response.json()

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert "results" in response_json
    assert len(response_json["results"]) == 1
    assert response_json["results"][0]["title"] == "Test Issue"


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
                "web_url": "https://gitlab.example.com/testgroup/testrepo/-/merge_requests/1",
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

    url = reverse(
        "api-v1:projects:get-gitlab-merge-requests",
        args=[project.id],
    )
    data = {"gitlab_project_id": 1}

    # When
    response = admin_client_new.get(url, data=data)
    response_json = response.json()

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert "results" in response_json
    assert len(response_json["results"]) == 1
    assert response_json["results"][0]["title"] == "Test MR"
    assert response_json["results"][0]["merged"] is False


# ---------------------------------------------------------------
# fetch_issues / fetch_merge_requests - missing config
# ---------------------------------------------------------------


def test_fetch_issues__missing_config__returns_400(
    admin_client_new: APIClient,
    project: Project,
) -> None:
    # Given - no gitlab_configuration
    url = reverse(
        "api-v1:projects:get-gitlab-issues",
        args=[project.id],
    )

    # When
    response = admin_client_new.get(url, data={"gitlab_project_id": 1})

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "doesn't have a valid GitLab Configuration" in response.json()["detail"]


def test_fetch_merge_requests__missing_config__returns_400(
    admin_client_new: APIClient,
    project: Project,
) -> None:
    # Given - no gitlab_configuration
    url = reverse(
        "api-v1:projects:get-gitlab-merge-requests",
        args=[project.id],
    )

    # When
    response = admin_client_new.get(url, data={"gitlab_project_id": 1})

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "doesn't have a valid GitLab Configuration" in response.json()["detail"]


# ---------------------------------------------------------------
# fetch_project_members tests
# ---------------------------------------------------------------


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
                "avatar_url": "https://gitlab.example.com/avatar/jdoe",
                "name": "John Doe",
            }
        ],
        headers={"x-page": "1", "x-total-pages": "1"},
    )

    url = reverse(
        "api-v1:projects:get-gitlab-project-members",
        args=[project.id],
    )

    # When
    response = admin_client_new.get(url, data={"gitlab_project_id": 1})
    response_json = response.json()

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert "results" in response_json
    assert len(response_json["results"]) == 1
    assert response_json["results"][0]["username"] == "jdoe"


# ---------------------------------------------------------------
# create_cleanup_issue tests
# ---------------------------------------------------------------


@pytest.mark.django_db
@responses.activate
def test_create_cleanup_issue__valid_feature_with_code_refs__returns_204(
    admin_client_new: APIClient,
    project: Project,
    feature: Feature,
    gitlab_configuration: GitLabConfiguration,
    mocker: MockerFixture,
) -> None:
    # Given
    from datetime import datetime

    from projects.code_references.types import (
        CodeReference,
        FeatureFlagCodeReferencesRepositorySummary,
        VCSProvider,
    )

    summary = FeatureFlagCodeReferencesRepositorySummary(
        repository_url="https://gitlab.example.com/testgroup/testrepo",
        vcs_provider=VCSProvider.GITLAB,
        revision="abc123",
        last_successful_repository_scanned_at=datetime.now(),
        last_feature_found_at=datetime.now(),
        code_references=[
            CodeReference(
                feature_name=feature.name,
                file_path="src/main.py",
                line_number=10,
                permalink="https://gitlab.example.com/testgroup/testrepo/-/blob/abc123/src/main.py#L10",
            )
        ],
    )
    mocker.patch(
        "integrations.gitlab.views.get_code_references_for_feature_flag",
        return_value=[summary],
    )
    responses.add(
        responses.POST,
        f"{GITLAB_INSTANCE_URL}/api/v4/projects/1/issues",
        json={
            "iid": 42,
            "title": f"Remove stale feature flag: {feature.name}",
            "state": "opened",
            "web_url": f"{GITLAB_INSTANCE_URL}/testgroup/testrepo/-/issues/42",
        },
        status=201,
    )
    mocker.patch(
        "features.feature_external_resources.models.FeatureExternalResource._handle_gitlab_after_save"
    )

    url = reverse(
        "api-v1:projects:create-gitlab-cleanup-issue",
        args=[project.id],
    )

    # When
    response = admin_client_new.post(url, data={"feature_id": feature.id})

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
def test_create_cleanup_issue__missing_feature__returns_404(
    admin_client_new: APIClient,
    project: Project,
    gitlab_configuration: GitLabConfiguration,
) -> None:
    # Given
    url = reverse(
        "api-v1:projects:create-gitlab-cleanup-issue",
        args=[project.id],
    )

    # When
    response = admin_client_new.post(url, data={"feature_id": 999999})

    # Then
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "Feature not found" in response.json()["detail"]


@pytest.mark.django_db
def test_create_cleanup_issue__no_code_references__returns_400(
    admin_client_new: APIClient,
    project: Project,
    feature: Feature,
    gitlab_configuration: GitLabConfiguration,
    mocker: MockerFixture,
) -> None:
    # Given
    mocker.patch(
        "integrations.gitlab.views.get_code_references_for_feature_flag",
        return_value=[],
    )

    url = reverse(
        "api-v1:projects:create-gitlab-cleanup-issue",
        args=[project.id],
    )

    # When
    response = admin_client_new.post(url, data={"feature_id": feature.id})

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "No code references found" in response.json()["detail"]


# ---------------------------------------------------------------
# gitlab_webhook additional tests
# ---------------------------------------------------------------


@pytest.mark.django_db
def test_gitlab_webhook__missing_config__returns_404(
    project: Project,
) -> None:
    # Given - no gitlab config exists for this project
    client = APIClient()
    url = reverse("api-v1:gitlab-webhook", args=[project.id])

    # When
    response = client.post(
        url,
        data=WEBHOOK_MR_PAYLOAD,
        content_type="application/json",
        **{  # type: ignore[arg-type]
            "HTTP_X_GITLAB_TOKEN": "some-secret",
            "HTTP_X_GITLAB_EVENT": "Merge Request Hook",
        },
    )

    # Then
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "No GitLab configuration found" in response.json()["error"]


@pytest.mark.django_db
def test_gitlab_webhook__unhandled_event_type__returns_200_bypassed(
    project: Project,
    gitlab_configuration: GitLabConfiguration,
) -> None:
    # Given
    client = APIClient()
    url = reverse("api-v1:gitlab-webhook", args=[project.id])
    payload = json.dumps({"object_kind": "push"})

    # When
    response = client.post(
        url,
        data=payload,
        content_type="application/json",
        **{  # type: ignore[arg-type]
            "HTTP_X_GITLAB_TOKEN": gitlab_configuration.webhook_secret,
            "HTTP_X_GITLAB_EVENT": "Push Hook",
        },
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["detail"] == "Event bypassed"


@pytest.mark.django_db
def test_gitlab_webhook__issue_event__returns_200(
    project: Project,
    gitlab_configuration: GitLabConfiguration,
) -> None:
    # Given
    client = APIClient()
    url = reverse("api-v1:gitlab-webhook", args=[project.id])
    payload = json.dumps(
        {
            "object_kind": "issue",
            "event_type": "issue",
            "project": {"path_with_namespace": "testgroup/testrepo"},
            "object_attributes": {
                "action": "open",
                "url": "https://gitlab.example.com/testgroup/testrepo/-/issues/1",
            },
        }
    )

    # When
    response = client.post(
        url,
        data=payload,
        content_type="application/json",
        **{  # type: ignore[arg-type]
            "HTTP_X_GITLAB_TOKEN": gitlab_configuration.webhook_secret,
            "HTTP_X_GITLAB_EVENT": "Issue Hook",
        },
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["detail"] == "Event processed"


# ---------------------------------------------------------------
# Error handler decorator tests
# ---------------------------------------------------------------


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
    url = reverse(
        "api-v1:projects:get-gitlab-issues",
        args=[project.id],
    )

    # When
    response = admin_client_new.get(url, data={"gitlab_project_id": 1})

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Failed to retrieve GitLab issues" in response.json()["detail"]


def test_gitlab_api_call_error_handler__request_exception__returns_502(
    admin_client_new: APIClient,
    project: Project,
    gitlab_configuration: GitLabConfiguration,
    mocker: MockerFixture,
) -> None:
    # Given
    import requests

    mocker.patch(
        "integrations.gitlab.views.fetch_search_gitlab_resource",
        side_effect=requests.RequestException("connection failed"),
    )
    url = reverse(
        "api-v1:projects:get-gitlab-issues",
        args=[project.id],
    )

    # When
    response = admin_client_new.get(url, data={"gitlab_project_id": 1})

    # Then
    assert response.status_code == status.HTTP_502_BAD_GATEWAY
    assert "Failed to retrieve GitLab issues" in response.json()["detail"]


# ---------------------------------------------------------------
# Permission tests
# ---------------------------------------------------------------


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


# ---------------------------------------------------------------
# GitLabConfigurationViewSet.get_queryset — real (non-swagger) path (line 122)
# ---------------------------------------------------------------


@pytest.mark.django_db
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


# ---------------------------------------------------------------
# fetch_merge_requests / fetch_issues — invalid query params (lines 157, 178)
# ---------------------------------------------------------------


@pytest.mark.django_db
def test_fetch_merge_requests__invalid_query_params__returns_400(
    admin_client_new: APIClient,
    project: Project,
    gitlab_configuration: GitLabConfiguration,
) -> None:
    # Given — non-integer page triggers serializer validation failure
    url = reverse(
        "api-v1:projects:get-gitlab-merge-requests",
        args=[project.id],
    )

    # When
    response = admin_client_new.get(url, data={"gitlab_project_id": "1", "page": "abc"})

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "error" in response.json()


@pytest.mark.django_db
def test_fetch_issues__invalid_query_params__returns_400(
    admin_client_new: APIClient,
    project: Project,
    gitlab_configuration: GitLabConfiguration,
) -> None:
    # Given — non-integer page triggers serializer validation failure
    url = reverse(
        "api-v1:projects:get-gitlab-issues",
        args=[project.id],
    )

    # When
    response = admin_client_new.get(url, data={"gitlab_project_id": "1", "page": "abc"})

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "error" in response.json()


# ---------------------------------------------------------------
# fetch_projects — invalid query params (line 198)
# ---------------------------------------------------------------


@pytest.mark.django_db
def test_fetch_projects__invalid_query_params__returns_400(
    admin_client_new: APIClient,
    project: Project,
    gitlab_configuration: GitLabConfiguration,
) -> None:
    # Given — non-integer page triggers serializer validation failure
    url = reverse(
        "api-v1:projects:get-gitlab-projects",
        args=[project.id],
    )

    # When
    response = admin_client_new.get(url, data={"page": "abc"})

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "error" in response.json()


# ---------------------------------------------------------------
# fetch_project_members — invalid query params (line 218)
# ---------------------------------------------------------------


@pytest.mark.django_db
def test_fetch_project_members__invalid_query_params__returns_400(
    admin_client_new: APIClient,
    project: Project,
    gitlab_configuration: GitLabConfiguration,
) -> None:
    # Given — non-integer page triggers serializer validation failure
    url = reverse(
        "api-v1:projects:get-gitlab-project-members",
        args=[project.id],
    )

    # When
    response = admin_client_new.get(url, data={"gitlab_project_id": "1", "page": "abc"})

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "error" in response.json()


# ---------------------------------------------------------------
# create_cleanup_issue — invalid serializer data (line 237)
# ---------------------------------------------------------------


@pytest.mark.django_db
def test_create_cleanup_issue__invalid_serializer_data__returns_400(
    admin_client_new: APIClient,
    project: Project,
    gitlab_configuration: GitLabConfiguration,
) -> None:
    # Given — feature_id is missing entirely so the serializer is invalid
    url = reverse(
        "api-v1:projects:create-gitlab-cleanup-issue",
        args=[project.id],
    )

    # When
    response = admin_client_new.post(url, data={})

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "error" in response.json()


# ---------------------------------------------------------------
# create_cleanup_issue — project_name mismatch (line 283) and
#                        gitlab_project_id is None (line 286)
# ---------------------------------------------------------------


@pytest.mark.django_db
def test_create_cleanup_issue__project_name_does_not_match_repo__returns_204_with_no_issue(
    admin_client_new: APIClient,
    project: Project,
    feature: Feature,
    gitlab_configuration: GitLabConfiguration,
    mocker: MockerFixture,
) -> None:
    # Given — the summary repository URL does not match the gitlab config project_name
    from datetime import datetime

    from projects.code_references.types import (
        CodeReference,
        FeatureFlagCodeReferencesRepositorySummary,
        VCSProvider,
    )

    summary = FeatureFlagCodeReferencesRepositorySummary(
        repository_url="https://gitlab.example.com/other/different-repo",
        vcs_provider=VCSProvider.GITLAB,
        revision="abc123",
        last_successful_repository_scanned_at=datetime.now(),
        last_feature_found_at=datetime.now(),
        code_references=[
            CodeReference(
                feature_name=feature.name,
                file_path="src/main.py",
                line_number=5,
                permalink="https://gitlab.example.com/other/different-repo/-/blob/abc123/src/main.py#L5",
            )
        ],
    )
    mocker.patch(
        "integrations.gitlab.views.get_code_references_for_feature_flag",
        return_value=[summary],
    )

    url = reverse(
        "api-v1:projects:create-gitlab-cleanup-issue",
        args=[project.id],
    )

    # When
    response = admin_client_new.post(url, data={"feature_id": feature.id})

    # Then — skipped (project_name mismatch), still returns 204
    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
def test_create_cleanup_issue__gitlab_project_id_is_none__skips_issue_creation(
    admin_client_new: APIClient,
    project: Project,
    feature: Feature,
    mocker: MockerFixture,
) -> None:
    # Given — GitLabConfiguration has no gitlab_project_id set
    from datetime import datetime

    from projects.code_references.types import (
        CodeReference,
        FeatureFlagCodeReferencesRepositorySummary,
        VCSProvider,
    )

    gitlab_config_no_project = GitLabConfiguration.objects.create(
        project=project,
        gitlab_instance_url=GITLAB_INSTANCE_URL,
        access_token="no-project-token",
        webhook_secret="some-secret",
        project_name="testgroup/testrepo",
        gitlab_project_id=None,
    )

    summary = FeatureFlagCodeReferencesRepositorySummary(
        repository_url="https://gitlab.example.com/testgroup/testrepo",
        vcs_provider=VCSProvider.GITLAB,
        revision="abc123",
        last_successful_repository_scanned_at=datetime.now(),
        last_feature_found_at=datetime.now(),
        code_references=[
            CodeReference(
                feature_name=feature.name,
                file_path="src/main.py",
                line_number=5,
                permalink="https://gitlab.example.com/testgroup/testrepo/-/blob/abc123/src/main.py#L5",
            )
        ],
    )
    mocker.patch(
        "integrations.gitlab.views.get_code_references_for_feature_flag",
        return_value=[summary],
    )

    url = reverse(
        "api-v1:projects:create-gitlab-cleanup-issue",
        args=[project.id],
    )

    # When
    response = admin_client_new.post(url, data={"feature_id": feature.id})

    # Then — skipped due to missing gitlab_project_id, returns 204
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Cleanup
    gitlab_config_no_project.delete()


# ---------------------------------------------------------------
# create_cleanup_issue — IntegrityError on duplicate resource (lines 310-311)
# ---------------------------------------------------------------


@pytest.mark.django_db
@responses.activate
def test_create_cleanup_issue__duplicate_external_resource__swallows_integrity_error(
    admin_client_new: APIClient,
    project: Project,
    feature: Feature,
    gitlab_configuration: GitLabConfiguration,
    mocker: MockerFixture,
) -> None:
    # Given — pre-existing FeatureExternalResource with the same URL that would cause IntegrityError
    from datetime import datetime

    from projects.code_references.types import (
        CodeReference,
        FeatureFlagCodeReferencesRepositorySummary,
        VCSProvider,
    )

    issue_url = f"{GITLAB_INSTANCE_URL}/testgroup/testrepo/-/issues/99"

    mocker.patch(
        "features.feature_external_resources.models.FeatureExternalResource._handle_gitlab_after_save"
    )
    FeatureExternalResource.objects.create(
        url=issue_url,
        type="GITLAB_ISSUE",
        feature=feature,
        metadata='{"state": "opened", "title": "Pre-existing"}',
    )

    summary = FeatureFlagCodeReferencesRepositorySummary(
        repository_url="https://gitlab.example.com/testgroup/testrepo",
        vcs_provider=VCSProvider.GITLAB,
        revision="abc123",
        last_successful_repository_scanned_at=datetime.now(),
        last_feature_found_at=datetime.now(),
        code_references=[
            CodeReference(
                feature_name=feature.name,
                file_path="src/main.py",
                line_number=10,
                permalink="https://gitlab.example.com/testgroup/testrepo/-/blob/abc123/src/main.py#L10",
            )
        ],
    )
    mocker.patch(
        "integrations.gitlab.views.get_code_references_for_feature_flag",
        return_value=[summary],
    )
    responses.add(
        responses.POST,
        f"{GITLAB_INSTANCE_URL}/api/v4/projects/1/issues",
        json={
            "iid": 99,
            "title": f"Remove stale feature flag: {feature.name}",
            "state": "opened",
            "web_url": issue_url,
        },
        status=201,
    )

    url = reverse(
        "api-v1:projects:create-gitlab-cleanup-issue",
        args=[project.id],
    )

    # When — the create call will hit IntegrityError for the duplicate URL, which must be swallowed
    response = admin_client_new.post(url, data={"feature_id": feature.id})

    # Then — integrity error is caught (line 310-311) and we still return 204
    assert response.status_code == status.HTTP_204_NO_CONTENT
