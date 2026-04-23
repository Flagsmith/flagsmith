import json
import uuid
from typing import Any
from unittest.mock import MagicMock

import pytest
import requests
import responses
from django.urls import reverse
from pytest_lazy_fixtures import lazy_fixture
from pytest_mock import MockerFixture
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from environments.models import Environment
from features.feature_external_resources.models import FeatureExternalResource
from features.models import Feature
from integrations.github.constants import GITHUB_API_URL
from integrations.github.models import GithubConfiguration, GitHubRepository
from integrations.github.views import (  # type: ignore[attr-defined]
    github_api_call_error_handler,
    github_webhook_payload_is_valid,
)
from organisations.models import Organisation
from projects.models import Project
from users.models import FFAdminUser

WEBHOOK_PAYLOAD = json.dumps({"installation": {"id": 1234567}, "action": "deleted"})
WEBHOOK_PAYLOAD_WITH_AN_INVALID_INSTALLATION_ID = json.dumps(
    {"installation": {"id": 765432}, "action": "deleted"}
)
WEBHOOK_PAYLOAD_WITHOUT_INSTALLATION_ID = json.dumps(
    {"installation": {"test": 765432}, "action": "deleted"}
)
WEBHOOK_PAYLOAD_MERGED = json.dumps(
    {
        "pull_request": {
            "id": 1234567,
            "html_url": "https://github.com/repositoryownertest/repositorynametest/issues/11",
            "merged": True,
        },
        "repository": {
            "full_name": "repositoryownertest/repositorynametest",
        },
        "action": "closed",
    }
)

WEBHOOK_SIGNATURE = "sha1=57a1426e19cdab55dd6d0c191743e2958e50ccaa"
WEBHOOK_SIGNATURE_WITH_AN_INVALID_INSTALLATION_ID = (
    "sha1=081eef49d04df27552587d5df1c6b76e0fe20d21"
)
WEBHOOK_SIGNATURE_WITHOUT_INSTALLATION_ID = (
    "sha1=f99796bd3cebb902864e87ed960c5cca8772ff67"
)
WEBHOOK_MERGED_ACTION_SIGNATURE = "sha1=f3f7e1e9b43448d570451317447d3b4f8f8142de"
WEBHOOK_SECRET = "secret-key"


def test_get_github_configuration__no_configuration_exists__returns_200(
    admin_client_new: APIClient,
    organisation: Organisation,
) -> None:
    # Given
    url = reverse(
        "api-v1:organisations:integrations-github-list",
        kwargs={"organisation_pk": organisation.id},
    )
    # When
    response = admin_client_new.get(url)
    # Then
    assert response.status_code == status.HTTP_200_OK


def test_get_github_configuration__non_admin_user__returns_configuration(
    staff_client: APIClient,
    organisation: Organisation,
    github_configuration: GithubConfiguration,
) -> None:
    # Given
    url = reverse(
        "api-v1:organisations:integrations-github-list",
        kwargs={"organisation_pk": organisation.id},
    )
    # When
    response = staff_client.get(url)
    # Then
    github_configuration_res = response.json()["results"][0]
    assert response.status_code == status.HTTP_200_OK
    assert github_configuration_res["installation_id"] == "1234567"
    assert github_configuration_res["id"] == github_configuration.id


def test_create_github_configuration__valid_data__returns_201(
    admin_client_new: APIClient,
    organisation: Organisation,
) -> None:
    # Given
    data = {
        "installation_id": 7654321,
    }
    url = reverse(
        "api-v1:organisations:integrations-github-list",
        kwargs={"organisation_pk": organisation.id},
    )
    # When
    response = admin_client_new.post(url, data)
    # Then
    assert response.status_code == status.HTTP_201_CREATED


def test_create_github_configuration__duplicate_installation_id__returns_400(
    admin_client_new: APIClient,
    organisation: Organisation,
    github_configuration: GithubConfiguration,
) -> None:
    # Given
    data = {
        "installation_id": 1234567,
    }
    url = reverse(
        "api-v1:organisations:integrations-github-list",
        kwargs={"organisation_pk": organisation.id},
    )
    # When
    response = admin_client_new.post(url, data)
    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    assert (
        "Duplication error. The GitHub integration already created"
        in response.json()["detail"]
    )


def test_create_github_configuration__organisation_already_has_integration__returns_400(
    admin_client_new: APIClient,
    organisation: Organisation,
    github_configuration: GithubConfiguration,
) -> None:
    # Given
    data = {
        "installation_id": 7654321,
    }
    url = reverse(
        "api-v1:organisations:integrations-github-list",
        kwargs={"organisation_pk": organisation.id},
    )
    # When
    response = admin_client_new.post(url, data)
    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    assert (
        "Duplication error. The GitHub integration already created"
        in response.json()["detail"]
    )


@responses.activate
def test_delete_github_configuration__valid_configuration__returns_204(
    admin_client_new: APIClient,
    organisation: Organisation,
    github_configuration: GithubConfiguration,
    github_repository: GitHubRepository,
    mocker: MockerFixture,
) -> None:
    # Given
    url = reverse(
        "api-v1:organisations:integrations-github-detail",
        args=[
            organisation.id,
            github_configuration.id,
        ],
    )

    mock_generate_token = mocker.patch(
        "integrations.github.client.generate_jwt_token",
    )
    mock_generate_token.return_value = "mocked_token"
    responses.add(
        method="DELETE",
        url=f"{GITHUB_API_URL}app/installations/{github_configuration.installation_id}",
        status=204,
    )

    # When
    response = admin_client_new.delete(url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not GithubConfiguration.objects.filter(id=github_configuration.id).exists()


@responses.activate
def test_delete_github_configuration__github_returns_404__still_deletes_configuration(
    admin_client_new: APIClient,
    organisation: Organisation,
    github_configuration: GithubConfiguration,
    github_repository: GitHubRepository,
    mocker: MockerFixture,
) -> None:
    # Given
    url = reverse(
        "api-v1:organisations:integrations-github-detail",
        args=[
            organisation.id,
            github_configuration.id,
        ],
    )

    mock_generate_token = mocker.patch(
        "integrations.github.client.generate_jwt_token",
    )
    mock_generate_token.return_value = "mocked_token"
    responses.add(
        method="DELETE",
        url=f"{GITHUB_API_URL}app/installations/{github_configuration.installation_id}",
        status=404,
        json={"message": "Not Found", "status": "404"},
    )

    # When
    response = admin_client_new.delete(url)
    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not GithubConfiguration.objects.filter(id=github_configuration.id).exists()


def test_get_github_repository__valid_configuration__returns_200(  # type: ignore[no-untyped-def]
    admin_client_new: APIClient,
    organisation: Organisation,
    github_configuration: GithubConfiguration,
):
    # Given
    url = reverse(
        "api-v1:organisations:repositories-list",
        args=[organisation.id, github_configuration.id],
    )
    # When
    response = admin_client_new.get(url)
    # Then
    assert response.status_code == status.HTTP_200_OK


def test_get_github_repository__github_pk_not_a_number__returns_400(  # type: ignore[no-untyped-def]
    admin_client_new: APIClient,
    organisation: Organisation,
    github_configuration: GithubConfiguration,
):
    # Given
    url = reverse(
        "api-v1:organisations:repositories-list",
        args=[organisation.id, "str"],
    )
    # When
    response = admin_client_new.get(url)
    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"github_pk": ["Must be an integer"]}


@responses.activate
def test_create_github_repository__valid_data__returns_201(
    admin_client_new: APIClient,
    organisation: Organisation,
    github_configuration: GithubConfiguration,
    project: Project,
    mocker: MockerFixture,
    mock_github_client_generate_token: MagicMock,
) -> None:
    # Given
    data = {
        "github_configuration": github_configuration.id,
        "repository_owner": "repositoryowner",
        "repository_name": "repositoryname",
        "project": project.id,
        "tagging_enabled": True,
    }

    responses.add(
        method="POST",
        url=f"{GITHUB_API_URL}repos/repositoryowner/repositoryname/labels",
        status=status.HTTP_200_OK,
        json={},
    )

    url = reverse(
        "api-v1:organisations:repositories-list",
        args=[organisation.id, github_configuration.id],
    )
    # When
    response = admin_client_new.post(url, data)

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert GitHubRepository.objects.filter(repository_owner="repositoryowner").exists()


@responses.activate
def test_create_github_repository__label_already_exists__returns_201_with_warning(
    admin_client_new: APIClient,
    organisation: Organisation,
    github_configuration: GithubConfiguration,
    project: Project,
    mocker: MockerFixture,
    mock_github_client_generate_token: MagicMock,
) -> None:
    # Given
    mocker_logger = mocker.patch("integrations.github.client.logger")

    data = {
        "github_configuration": github_configuration.id,
        "repository_owner": "repositoryowner",
        "repository_name": "repositoryname",
        "project": project.id,
        "tagging_enabled": True,
    }

    mock_response = {
        "message": "Validation Failed",
        "errors": [{"resource": "Label", "code": "already_exists", "field": "name"}],
        "documentation_url": "https://docs.github.com/rest/issues/labels#create-a-label",
        "status": "422",
    }

    responses.add(
        method="POST",
        url=f"{GITHUB_API_URL}repos/repositoryowner/repositoryname/labels",
        status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        json=mock_response,
    )

    url = reverse(
        "api-v1:organisations:repositories-list",
        args=[organisation.id, github_configuration.id],
    )
    # When
    response = admin_client_new.post(url, data)

    # Then
    mocker_logger.warning.assert_called_once_with("Label already exists")
    assert response.status_code == status.HTTP_201_CREATED
    assert GitHubRepository.objects.filter(repository_owner="repositoryowner").exists()


def test_create_github_repository__no_permissions__returns_403(
    staff_client: APIClient,
    organisation: Organisation,
    github_configuration: GithubConfiguration,
    project: Project,
) -> None:
    # Given
    data = {
        "github_configuration": github_configuration.id,
        "repository_owner": "repositoryowner",
        "repository_name": "repositoryname",
        "project": project.id,
    }

    url = reverse(
        "api-v1:organisations:repositories-list",
        args=[organisation.id, github_configuration.id],
    )
    # When
    response = staff_client.post(url, data)

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_github_repository__duplicate_repository__returns_400(
    admin_client_new: APIClient,
    organisation: Organisation,
    github_configuration: GithubConfiguration,
    project: Project,
    github_repository: GitHubRepository,
) -> None:
    # Given
    data = {
        "github_configuration": github_configuration.id,
        "repository_owner": "repositoryownertest",
        "repository_name": "repositorynametest",
        "project": project.id,
    }

    url = reverse(
        "api-v1:organisations:repositories-list",
        args=[organisation.id, github_configuration.id],
    )

    # When
    response = admin_client_new.post(url, data)

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    assert (
        "Duplication error. The GitHub repository already linked" in response.json()[0]
    )


def test_delete_github_repository__valid_repository__removes_external_resources(
    admin_client_new: APIClient,
    organisation: Organisation,
    github_configuration: GithubConfiguration,
    github_repository: GitHubRepository,
    feature_external_resource: FeatureExternalResource,
    mock_github_client_generate_token: MagicMock,
) -> None:
    # Given
    url = reverse(
        "api-v1:organisations:repositories-detail",
        args=[organisation.id, github_configuration.id, github_repository.id],
    )
    for feature in github_repository.project.features.all():
        assert FeatureExternalResource.objects.filter(feature=feature).exists()

    # When
    response = admin_client_new.delete(url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    for feature in github_repository.project.features.all():
        assert not FeatureExternalResource.objects.filter(feature=feature).exists()


class MockResponse:
    def __init__(self, json_data, status_code):  # type: ignore[no-untyped-def]
        self.json_data = json_data
        self.status_code = status_code
        self.links = {
            "next": "https://example.com/next",
            "prev": "https://example.com/prev",
        }

    def raise_for_status(self) -> None:
        if 400 <= self.status_code < 600:
            raise requests.exceptions.HTTPError(f"HTTP Error {self.status_code}")

    def json(self):  # type: ignore[no-untyped-def]
        return self.json_data


def mocked_requests_get_issues_and_pull_requests(*args, **kwargs):  # type: ignore[no-untyped-def]
    json_data = {
        "items": [
            {
                "html_url": "https://example.com/1",
                "id": 1,
                "title": "Title 1",
                "number": 101,
                "state": "Open",
                "merged": False,
                "draft": True,
            },
        ],
        "total_count": 1,
        "incomplete_results": True,
    }
    status_code = 200
    response = MockResponse(json_data, status_code)  # type: ignore[no-untyped-call]

    return response


def mocked_requests_get_error(*args, **kwargs):  # type: ignore[no-untyped-def]
    json_data = {"detail": "Not found"}
    status_code = 404
    response = MockResponse(json_data, status_code)  # type: ignore[no-untyped-call]

    return response


def test_fetch_pull_requests__valid_request__returns_results(
    admin_client_new: APIClient,
    organisation: Organisation,
    github_configuration: GithubConfiguration,
    github_repository: GitHubRepository,
    mock_github_client_generate_token: MagicMock,
    mocker: MockerFixture,
) -> None:
    # Given
    github_request_mock = mocker.patch(
        "requests.get", side_effect=mocked_requests_get_issues_and_pull_requests
    )

    url = reverse("api-v1:organisations:get-github-pulls", args=[organisation.id])
    data = {"repo_owner": "owner", "repo_name": "repo"}

    # When
    response = admin_client_new.get(url, data=data)
    response_json = response.json()

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert "results" in response_json

    github_request_mock.assert_called_with(
        "https://api.github.com/search/issues?q= repo:owner/repo is:pr is:open in:title in:body&per_page=100&page=1",  # noqa: E501
        headers={
            "X-GitHub-Api-Version": "2022-11-28",
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "Bearer mocked_token",
        },
        timeout=10,
    )


def test_fetch_issues__valid_request_with_filters__returns_results(
    admin_client_new: APIClient,
    organisation: Organisation,
    github_configuration: GithubConfiguration,
    github_repository: GitHubRepository,
    mock_github_client_generate_token: MagicMock,
    mocker: MockerFixture,
) -> None:
    # Given
    github_request_mock = mocker.patch(
        "requests.get", side_effect=mocked_requests_get_issues_and_pull_requests
    )
    url = reverse("api-v1:organisations:get-github-issues", args=[organisation.id])
    data = {
        "repo_owner": "owner",
        "repo_name": "repo",
        "search_text": "search text",
        "search_in_comments": True,
        "author": "author",
        "assignee": "assignee",
    }
    # When
    response = admin_client_new.get(url, data=data)  # type: ignore[arg-type]

    # Then
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    assert "results" in response_json

    github_request_mock.assert_called_with(
        "https://api.github.com/search/issues?q= search text repo:owner/repo is:issue is:open in:title in:body in:comments author:author assignee:assignee&per_page=100&page=1",  # noqa: E501
        headers={
            "X-GitHub-Api-Version": "2022-11-28",
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "Bearer mocked_token",
        },
        timeout=10,
    )


@responses.activate
def test_fetch_issues__bad_response_from_github__returns_502(
    admin_client_new: APIClient,
    organisation: Organisation,
    github_configuration: GithubConfiguration,
    github_repository: GitHubRepository,
    mock_github_client_generate_token: MagicMock,
    mocker: MockerFixture,
) -> None:
    # Given

    mock_response = {
        "message": "Validation Failed",
        "errors": [{"message": "Error", "code": "not_found"}],
        "documentation_url": "https://docs.github.com/v3/search/",
        "status": "404",
    }

    responses.add(
        method="GET",
        url="https://api.github.com/search/issues?q=%20repo:repo/repo%20is:issue%20is:open%20in:title%20in:body&per_page=100&page=1",  # noqa: E501
        status=status.HTTP_404_NOT_FOUND,
        json=mock_response,
    )
    url = reverse("api-v1:organisations:get-github-issues", args=[organisation.id])
    data = {"repo_owner": "owner", "repo_name": "repo"}
    # When
    response = admin_client_new.get(url, data=data)

    # Then
    assert response.status_code == status.HTTP_502_BAD_GATEWAY
    assert "Failed to retrieve GitHub issues." in response.json()["detail"]


@responses.activate
def test_search_issues__invalid_search_params__returns_400(
    admin_client_new: APIClient,
    organisation: Organisation,
    github_configuration: GithubConfiguration,
    github_repository: GitHubRepository,
    mock_github_client_generate_token: MagicMock,
    mocker: MockerFixture,
) -> None:
    # Given
    mock_response = {
        "message": "Validation Failed",
        "errors": [{"message": "Error", "code": "invalid"}],
        "documentation_url": "https://docs.github.com/v3/search/",
        "status": "422",
    }
    responses.add(
        method="GET",
        url="https://api.github.com/search/issues?q=%20repo:owner/repo%20is:issue%20is:open%20in:title%20in:body&per_page=100&page=1",  # noqa: E501
        status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        json=mock_response,
    )
    url = reverse("api-v1:organisations:get-github-issues", args=[organisation.id])
    data = {"repo_owner": "owner", "repo_name": "repo"}
    # When
    response = admin_client_new.get(url, data=data)

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    response_json = response.json()
    assert (
        "Failed to retrieve GitHub issues. Error: The resources do not exist or you do not have permission to view them"
        in response_json["detail"]
    )


@responses.activate
def test_fetch_repositories__valid_installation__returns_repositories(
    admin_client_new: APIClient,
    organisation: Organisation,
    github_configuration: GithubConfiguration,
    github_repository: GitHubRepository,
    mock_github_client_generate_token: MagicMock,
) -> None:
    # Given
    responses.add(
        method="GET",
        url=f"{GITHUB_API_URL}installation/repositories",
        status=status.HTTP_200_OK,
        json={
            "repositories": [
                {
                    "full_name": "owner/repo-name",
                    "id": 1,
                    "name": "repo-name",
                },
            ],
            "total_count": 1,
        },
    )

    url = reverse(
        "api-v1:organisations:get-github-installation-repos", args=[organisation.id]
    )
    # When
    response = admin_client_new.get(
        url, data={"installation_id": github_configuration.installation_id}
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    assert "results" in response_json
    assert len(response_json["results"]) == 1


@pytest.mark.parametrize(
    "client, reverse_url",
    [
        (
            lazy_fixture("admin_master_api_key_client"),
            "api-v1:organisations:get-github-issues",
        ),
        (
            lazy_fixture("admin_master_api_key_client"),
            "api-v1:organisations:get-github-pulls",
        ),
        (lazy_fixture("admin_client"), "api-v1:organisations:get-github-issues"),
        (lazy_fixture("admin_client"), "api-v1:organisations:get-github-pulls"),
    ],
)
def test_fetch_issues_and_pulls__integration_not_configured__returns_400(
    client: APIClient,
    organisation: Organisation,
    reverse_url: str,
    mock_github_client_generate_token: MagicMock,
) -> None:
    # Given / When
    url = reverse(reverse_url, args=[organisation.id])
    response = client.get(url)

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.parametrize(
    "reverse_url",
    [
        ("api-v1:organisations:get-github-issues"),
        ("api-v1:organisations:get-github-pulls"),
    ],
)
def test_fetch_issues_or_pulls__user_not_in_organisation__returns_403(
    api_client: APIClient,
    organisation: Organisation,
    github_configuration: GithubConfiguration,
    github_repository: GitHubRepository,
    mock_github_client_generate_token: MagicMock,
    reverse_url: str,
) -> None:
    # Given
    url = reverse(reverse_url, args=[organisation.id])

    user = FFAdminUser.objects.create(email=f"user{uuid.uuid4()}@example.com")
    api_client.force_authenticate(user)

    # When
    response = api_client.get(url)

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_github_webhook_payload_is_valid__valid_payload__returns_true() -> None:
    # Given
    payload_body = WEBHOOK_PAYLOAD.encode("utf-8")

    # When
    result = github_webhook_payload_is_valid(
        payload_body=payload_body,
        secret_token=WEBHOOK_SECRET,
        signature_header=WEBHOOK_SIGNATURE,
    )

    # Then
    assert result is True


def test_github_webhook_payload_is_valid__bad_signature__returns_false() -> None:
    # Given
    payload_body = WEBHOOK_PAYLOAD.encode("utf-8")

    # When
    result = github_webhook_payload_is_valid(
        payload_body=payload_body,
        secret_token=WEBHOOK_SECRET,
        signature_header="sha1=757107ea0eb2509fc211221cce984b8a37570b6d7586c22c46f4379c8b043e18",
    )

    # Then
    assert result is False


def test_github_webhook_payload_is_valid__no_signature_header__returns_false() -> None:
    # Given
    payload_body = WEBHOOK_PAYLOAD.encode("utf-8")

    # When
    result = github_webhook_payload_is_valid(
        payload_body=payload_body,
        secret_token=WEBHOOK_SECRET,
        signature_header=None,  # type: ignore[arg-type]
    )

    # Then
    assert result is False


def test_github_webhook__delete_installation_event__removes_configuration(  # type: ignore[no-untyped-def]
    api_client: APIClient,
    github_configuration: GithubConfiguration,
    set_github_webhook_secret,
) -> None:
    # Given
    url = reverse("api-v1:github-webhook")

    # When
    response = api_client.post(
        path=url,
        data=WEBHOOK_PAYLOAD,
        content_type="application/json",
        HTTP_X_HUB_SIGNATURE=WEBHOOK_SIGNATURE,
        HTTP_X_GITHUB_EVENT="installation",
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert not GithubConfiguration.objects.filter(installation_id=1234567).exists()


def test_github_webhook__merged_pull_request__tags_feature(  # type: ignore[no-untyped-def]
    api_client: APIClient,
    feature: Feature,
    github_configuration: GithubConfiguration,
    github_repository: GitHubRepository,
    feature_external_resource: FeatureExternalResource,
    set_github_webhook_secret,
) -> None:
    # Given
    url = reverse("api-v1:github-webhook")

    # When
    response = api_client.post(
        path=url,
        data=WEBHOOK_PAYLOAD_MERGED,
        content_type="application/json",
        HTTP_X_HUB_SIGNATURE=WEBHOOK_MERGED_ACTION_SIGNATURE,
        HTTP_X_GITHUB_EVENT="pull_request",
    )

    # Then
    feature.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert feature.tags.first().label == "PR Merged"  # type: ignore[union-attr]


def test_github_webhook__missing_installation_id__logs_error(  # type: ignore[no-untyped-def]
    api_client: APIClient,
    mocker: MockerFixture,
    set_github_webhook_secret,
) -> None:
    # Given
    url = reverse("api-v1:github-webhook")
    mocker_logger = mocker.patch("integrations.github.github.logger")

    # When
    response = api_client.post(
        path=url,
        data=WEBHOOK_PAYLOAD_WITHOUT_INSTALLATION_ID,
        content_type="application/json",
        HTTP_X_HUB_SIGNATURE=WEBHOOK_SIGNATURE_WITHOUT_INSTALLATION_ID,
        HTTP_X_GITHUB_EVENT="installation",
    )

    # Then
    mocker_logger.error.assert_called_once_with(
        "The installation_id is not present in the payload: {'installation': {'test': 765432}, 'action': 'deleted'}"
    )
    assert response.status_code == status.HTTP_200_OK


def test_github_webhook__non_existing_installation__logs_error(  # type: ignore[no-untyped-def]
    api_client: APIClient,
    github_configuration: GithubConfiguration,
    mocker: MockerFixture,
    set_github_webhook_secret,
) -> None:
    # Given
    url = reverse("api-v1:github-webhook")
    mocker_logger = mocker.patch("integrations.github.github.logger")

    # When
    response = api_client.post(
        path=url,
        data=WEBHOOK_PAYLOAD_WITH_AN_INVALID_INSTALLATION_ID,
        content_type="application/json",
        HTTP_X_HUB_SIGNATURE=WEBHOOK_SIGNATURE_WITH_AN_INVALID_INSTALLATION_ID,
        HTTP_X_GITHUB_EVENT="installation",
    )

    # Then
    mocker_logger.error.assert_called_once_with(
        "GitHub Configuration with installation_id 765432 does not exist"
    )
    assert response.status_code == status.HTTP_200_OK


def test_github_webhook__missing_signature_header__returns_400(  # type: ignore[no-untyped-def]
    github_configuration: GithubConfiguration,
    set_github_webhook_secret,
) -> None:
    # Given
    url = reverse("api-v1:github-webhook")

    # When
    client = APIClient()
    response = client.post(
        path=url,
        data=WEBHOOK_PAYLOAD,
        content_type="application/json",
        HTTP_X_GITHUB_EVENT="installation",
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"error": "Invalid signature"}
    assert GithubConfiguration.objects.filter(installation_id=1234567).exists()


def test_github_webhook__bad_signature_header__returns_400(  # type: ignore[no-untyped-def]
    github_configuration: GithubConfiguration,
    set_github_webhook_secret,
) -> None:
    # Given
    url = reverse("api-v1:github-webhook")

    # When
    client = APIClient()
    response = client.post(
        path=url,
        data=WEBHOOK_PAYLOAD,
        content_type="application/json",
        HTTP_X_HUB_SIGNATURE="sha1=757107ea0eb2509fc211221cce984b8a37570b6d7586c22c46f4379c8b043e18",
        HTTP_X_GITHUB_EVENT="installation",
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert GithubConfiguration.objects.filter(installation_id=1234567).exists()
    assert response.json() == {"error": "Invalid signature"}


def test_github_webhook__unhandled_event_type__bypasses_processing(  # type: ignore[no-untyped-def]
    github_configuration: GithubConfiguration,
    set_github_webhook_secret,
) -> None:
    # Given
    url = reverse("api-v1:github-webhook")

    # When
    client = APIClient()
    response = client.post(
        path=url,
        data=WEBHOOK_PAYLOAD,
        content_type="application/json",
        HTTP_X_HUB_SIGNATURE=WEBHOOK_SIGNATURE,
        HTTP_X_GITHUB_EVENT="installation_repositories",
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert GithubConfiguration.objects.filter(installation_id=1234567).exists()


@responses.activate
def test_fetch_pull_requests__github_request_failed__returns_502(
    admin_client_new: APIClient,
    organisation: Organisation,
    github_configuration: GithubConfiguration,
    github_repository: GitHubRepository,
    mock_github_client_generate_token: MagicMock,
) -> None:
    # Given
    data = {"repo_owner": "owner", "repo_name": "repo"}
    responses.add(
        method="GET",
        url=f"{GITHUB_API_URL}repos/{data['repo_owner']}/{data['repo_name']}/pulls",
        status=404,
    )

    url = reverse("api-v1:organisations:get-github-pulls", args=[organisation.id])
    data = {"repo_owner": "owner", "repo_name": "repo"}

    # When
    response = admin_client_new.get(url, data=data)
    response_json = response.json()

    # Then
    assert response.status_code == status.HTTP_502_BAD_GATEWAY
    assert "Failed to retrieve GitHub pull requests." in response_json["detail"]


@responses.activate
def test_fetch_pulls__invalid_github_response__returns_502(
    admin_client_new: APIClient,
    organisation: Organisation,
    github_configuration: GithubConfiguration,
    github_repository: GitHubRepository,
    mock_github_client_generate_token: MagicMock,
) -> None:
    # Given
    data = {"repo_owner": "owner", "repo_name": "repo"}
    responses.add(
        method="GET",
        url=f"{GITHUB_API_URL}repos/{data['repo_owner']}/{data['repo_name']}/pulls",
        status=200,
        json={"details": "invalid"},
    )
    url = reverse("api-v1:organisations:get-github-issues", args=[organisation.id])
    data = {"repo_owner": "owner", "repo_name": "repo"}
    # When
    response = admin_client_new.get(url, data=data)

    # Then
    assert response.status_code == status.HTTP_502_BAD_GATEWAY


def test_fetch_repositories__no_installation_id__returns_400(
    admin_client_new: APIClient,
    organisation: Organisation,
) -> None:
    # Given
    url = reverse(
        "api-v1:organisations:get-github-installation-repos", args=[organisation.id]
    )
    # When
    response = admin_client_new.get(url)
    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Missing installation_id parameter"}


@responses.activate
def test_fetch_repo_contributors__valid_request__returns_contributors(
    admin_client_new: APIClient,
    organisation: Organisation,
    github_configuration: GithubConfiguration,
    github_repository: GitHubRepository,
    mock_github_client_generate_token: MagicMock,
) -> None:
    # Given
    url = reverse(
        viewname="api-v1:organisations:get-github-repo-contributors",
        args=[organisation.id],
    )

    mocked_github_response = [
        {
            "login": "contributor1",
            "avatar_url": "https://example.com/avatar1",
            "contributions": 150,
        },
        {
            "login": "contributor2",
            "avatar_url": "https://example.com/avatar2",
            "contributions": 110,
        },
        {
            "login": "contributor3",
            "avatar_url": "https://example.com/avatar3",
            "contributions": 12,
        },
    ]

    expected_response = {"results": mocked_github_response}

    # Add response for endpoint being tested
    responses.add(
        method=responses.GET,
        url=(
            f"{GITHUB_API_URL}repos/{github_repository.repository_owner}/{github_repository.repository_name}/"
            "contributors?&per_page=100&page=1"
        ),
        json=mocked_github_response,
        status=200,
    )

    # When
    response = admin_client_new.get(
        path=url,
        data={
            "repo_owner": github_repository.repository_owner,
            "repo_name": github_repository.repository_name,
        },
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response


def test_fetch_repo_contributors__missing_query_params__returns_400(
    admin_client_new: APIClient,
    organisation: Organisation,
    github_configuration: GithubConfiguration,
    github_repository: GitHubRepository,
) -> None:
    # Given
    url = reverse(
        viewname="api-v1:organisations:get-github-repo-contributors",
        args=[organisation.id],
    )

    # When
    response = admin_client_new.get(
        path=url,
        data={
            "repo_owner": github_repository.repository_owner,
        },
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"error": {"repo_name": ["This field is required."]}}


def test_github_api_call_error_handler__value_error_raised__returns_400(
    mocker: MockerFixture,
) -> None:
    # Given
    @github_api_call_error_handler()
    def test_view(request):  # type: ignore[no-untyped-def]
        raise ValueError("Invalid parameter")

    # When
    response = test_view(None)

    # Then
    assert isinstance(response, Response)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data == {
        "detail": "Failed to retrieve requested information from GitHub API. Error: Invalid parameter"
    }


@pytest.mark.parametrize(
    "page, page_size, error_detail",
    [
        (
            1,
            103,
            "Failed to retrieve GitHub repositories. Error: Page size must be an integer between 1 and 100",
        ),
        (
            0,
            100,
            "Failed to retrieve GitHub repositories. Error: Page must be greater or equal than 1",
        ),
    ],
)
def test_fetch_repositories__invalid_page_or_page_size_value__returns_400(
    admin_client: APIClient,
    organisation: Organisation,
    github_configuration: GithubConfiguration,
    github_repository: GitHubRepository,
    page: int,
    page_size: int,
    error_detail: str,
) -> None:
    # Given
    data: dict[str, str | int] = {
        "installation_id": github_configuration.installation_id,
        "page": page,
        "page_size": page_size,
    }

    url = reverse(
        "api-v1:organisations:get-github-installation-repos", args=[organisation.id]
    )
    # When
    response = admin_client.get(url, data)

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    response_json = response.json()
    assert response_json == {"detail": error_detail}


@pytest.mark.parametrize(
    "page, page_size, error_response",
    [
        (
            1,
            "string",
            {"error": {"page_size": ["A valid integer is required."]}},
        ),
        (
            "string",
            100,
            {"error": {"page": ["A valid integer is required."]}},
        ),
    ],
)
def test_fetch_repositories__invalid_page_or_page_size_type__returns_400(
    admin_client: APIClient,
    organisation: Organisation,
    github_configuration: GithubConfiguration,
    github_repository: GitHubRepository,
    page: int,
    page_size: int,
    error_response: dict[str, Any],
) -> None:
    # Given
    data: dict[str, str | int] = {
        "installation_id": github_configuration.installation_id,
        "page": page,
        "page_size": page_size,
    }

    url = reverse(
        "api-v1:organisations:get-github-installation-repos", args=[organisation.id]
    )
    # When
    response = admin_client.get(url, data)

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    response_json = response.json()
    assert response_json == error_response


@responses.activate
def test_create_feature_external_resource__tagging_disabled__does_not_add_tags(
    admin_client_new: APIClient,
    project: Project,
    environment: Environment,
    github_repository: GitHubRepository,
    feature_with_value: Feature,
    mock_github_client_generate_token: MagicMock,
    post_request_mock: MagicMock,
) -> None:
    # Given
    github_repository.tagging_enabled = False
    github_repository.save()
    repository_owner_name = (
        f"{github_repository.repository_owner}/{github_repository.repository_name}"
    )

    feature_external_resource_data = {
        "type": "GITHUB_ISSUE",
        "url": f"https://github.com/{repository_owner_name}/issues/35",
        "feature": feature_with_value.id,
        "metadata": {"state": "open"},
    }

    url = reverse(
        "api-v1:projects:feature-external-resources-list",
        kwargs={"project_pk": project.id, "feature_pk": feature_with_value.id},
    )

    # When
    response = admin_client_new.post(
        url, data=feature_external_resource_data, format="json"
    )

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert feature_with_value.tags.count() == 0


@responses.activate
def test_update_github_repository__enable_tagging__creates_label(
    admin_client_new: APIClient,
    organisation: Organisation,
    github_configuration: GithubConfiguration,
    github_repository: GitHubRepository,
    project: Project,
    mocker: MockerFixture,
    mock_github_client_generate_token: MagicMock,
) -> None:
    # Given
    github_repository.tagging_enabled = False
    github_repository.save()
    data = {
        "github_configuration": github_configuration.id,
        "repository_owner": "repositoryowner",
        "repository_name": "repositoryname",
        "project": project.id,
        "tagging_enabled": True,
    }

    responses.add(
        method="POST",
        url=f"{GITHUB_API_URL}repos/repositoryowner/repositoryname/labels",
        status=status.HTTP_200_OK,
        json={},
    )

    url = reverse(
        "api-v1:organisations:repositories-detail",
        args=[organisation.id, github_configuration.id, github_repository.id],
    )
    # When
    response = admin_client_new.put(url, data)

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert GitHubRepository.objects.filter(repository_owner="repositoryowner").exists()
    assert GitHubRepository.objects.get(
        repository_owner="repositoryowner"
    ).tagging_enabled
