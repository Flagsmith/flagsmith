import json
from typing import Any

import pytest
import requests
import responses
from django.conf import settings
from django.urls import reverse
from pytest_lazyfixture import lazy_fixture
from pytest_mock import MockerFixture
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from features.feature_external_resources.models import FeatureExternalResource
from integrations.github.constants import GITHUB_API_URL
from integrations.github.models import GithubConfiguration, GithubRepository
from integrations.github.views import (
    github_api_call_error_handler,
    github_webhook_payload_is_valid,
)
from organisations.models import Organisation
from projects.models import Project

WEBHOOK_PAYLOAD = json.dumps({"installation": {"id": 1234567}, "action": "deleted"})
WEBHOOK_PAYLOAD_WITH_AN_INVALID_INSTALLATION_ID = json.dumps(
    {"installation": {"id": 765432}, "action": "deleted"}
)
WEBHOOK_PAYLOAD_WITHOUT_INSTALLATION_ID = json.dumps(
    {"installation": {"test": 765432}, "action": "deleted"}
)
WEBHOOK_SIGNATURE = "sha1=57a1426e19cdab55dd6d0c191743e2958e50ccaa"
WEBHOOK_SIGNATURE_WITH_AN_INVALID_INSTALLATION_ID = (
    "sha1=081eef49d04df27552587d5df1c6b76e0fe20d21"
)
WEBHOOK_SIGNATURE_WITHOUT_INSTALLATION_ID = (
    "sha1=f99796bd3cebb902864e87ed960c5cca8772ff67"
)
WEBHOOK_SECRET = "secret-key"


def test_get_github_configuration(
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


def test_non_admin_user_get_github_configuration(
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


def test_create_github_configuration(
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


def test_cannot_create_github_configuration_due_to_unique_constraint(
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


def test_cannot_create_github_configuration_when_the_organization_already_has_an_integration(
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
def test_delete_github_configuration(
    admin_client_new: APIClient,
    organisation: Organisation,
    github_configuration: GithubConfiguration,
    github_repository: GithubRepository,
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
def test_cannot_delete_github_configuration_when_delete_github_installation_response_was_404(
    admin_client_new: APIClient,
    organisation: Organisation,
    github_configuration: GithubConfiguration,
    github_repository: GithubRepository,
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
        json={"message": "not found"},
    )

    # When
    response = admin_client_new.delete(url)
    # Then
    assert response.status_code == status.HTTP_502_BAD_GATEWAY
    assert (
        response.json()["detail"]
        == "Failed to delete GitHub Installation. Error: 404 Client Error: Not Found for url: https://api.github.com/app/installations/1234567"  # noqa: E501
    )
    assert GithubConfiguration.objects.filter(id=github_configuration.id).exists()


def test_get_github_repository(
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


def test_cannot_get_github_repository_when_github_pk_in_not_a_number(
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


def test_create_github_repository(
    admin_client_new: APIClient,
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
    response = admin_client_new.post(url, data)

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert GithubRepository.objects.filter(repository_owner="repositoryowner").exists()


def test_cannot_create_github_repository_when_does_not_have_permissions(
    test_user_client: APIClient,
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
    response = test_user_client.post(url, data)

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_cannot_create_github_repository_due_to_unique_constraint(
    admin_client_new: APIClient,
    organisation: Organisation,
    github_configuration: GithubConfiguration,
    project: Project,
    github_repository: GithubRepository,
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


def test_github_delete_repository(
    admin_client_new: APIClient,
    organisation: Organisation,
    github_configuration: GithubConfiguration,
    github_repository: GithubRepository,
    feature_external_resource: FeatureExternalResource,
    mocker: MockerFixture,
) -> None:
    # Given
    mock_generate_token = mocker.patch(
        "integrations.github.client.generate_token",
    )
    mock_generate_token.return_value = "mocked_token"
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
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code
        self.links = {
            "next": "https://example.com/next",
            "prev": "https://example.com/prev",
        }

    def raise_for_status(self) -> None:
        if 400 <= self.status_code < 600:
            raise requests.exceptions.HTTPError(f"HTTP Error {self.status_code}")

    def json(self):
        return self.json_data


def mocked_requests_get_issues_and_pull_requests(*args, **kwargs):
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
    response = MockResponse(json_data, status_code)

    return response


def mocked_requests_get_error(*args, **kwargs):
    json_data = {"detail": "Not found"}
    status_code = 404
    response = MockResponse(json_data, status_code)

    return response


def test_fetch_pull_requests(
    admin_client_new: APIClient,
    organisation: Organisation,
    github_configuration: GithubConfiguration,
    github_repository: GithubRepository,
    mocker: MockerFixture,
) -> None:

    # Given
    mock_generate_token = mocker.patch(
        "integrations.github.client.generate_token",
    )
    mock_generate_token.return_value = "mocked_token"
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


def test_fetch_issues(
    admin_client_new: APIClient,
    organisation: Organisation,
    github_configuration: GithubConfiguration,
    github_repository: GithubRepository,
    mocker: MockerFixture,
) -> None:
    # Given
    mock_generate_token = mocker.patch(
        "integrations.github.client.generate_token",
    )
    mock_generate_token.return_value = "mocked_token"
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
    response = admin_client_new.get(url, data=data)

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


def test_fetch_issues_returns_error_on_bad_response_from_github(
    admin_client_new: APIClient,
    organisation: Organisation,
    github_configuration: GithubConfiguration,
    github_repository: GithubRepository,
    mocker: MockerFixture,
) -> None:
    # Given
    mock_generate_token = mocker.patch(
        "integrations.github.client.generate_token",
    )
    mock_generate_token.return_value = "mocked_token"
    mocker.patch("requests.get", side_effect=mocked_requests_get_error)
    url = reverse("api-v1:organisations:get-github-issues", args=[organisation.id])
    data = {"repo_owner": "owner", "repo_name": "repo"}
    # When
    response = admin_client_new.get(url, data=data)

    # Then
    assert response.status_code == status.HTTP_502_BAD_GATEWAY
    response_json = response.json()
    assert (
        "Failed to retrieve GitHub issues. Error: HTTP Error 404"
        in response_json["detail"]
    )


@responses.activate
def test_fetch_repositories(
    admin_client_new: APIClient,
    organisation: Organisation,
    github_configuration: GithubConfiguration,
    github_repository: GithubRepository,
    mocker: MockerFixture,
) -> None:
    # Given
    mock_generate_token = mocker.patch(
        "integrations.github.client.generate_token",
    )
    mock_generate_token.return_value = "mocked_token"
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
def test_fetch_issues_and_pull_requests_fails_with_status_400_when_integration_not_configured(
    client: APIClient, organisation: Organisation, reverse_url: str, mocker
) -> None:
    # Given
    mock_generate_token = mocker.patch(
        "integrations.github.client.generate_token",
    )
    mock_generate_token.generate_token.return_value = "mocked_token"
    # When
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
def test_cannot_fetch_issues_or_prs_when_does_not_have_permissions(
    test_user_client: APIClient,
    organisation: Organisation,
    github_configuration: GithubConfiguration,
    github_repository: GithubRepository,
    mocker,
    reverse_url: str,
) -> None:
    # Given
    mock_generate_token = mocker.patch(
        "integrations.github.client.generate_token",
    )
    mock_generate_token.generate_token.return_value = "mocked_token"

    # When
    url = reverse(reverse_url, args=[organisation.id])
    response = test_user_client.get(url)

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_verify_github_webhook_payload() -> None:
    # When
    result = github_webhook_payload_is_valid(
        payload_body=WEBHOOK_PAYLOAD.encode("utf-8"),
        secret_token=WEBHOOK_SECRET,
        signature_header=WEBHOOK_SIGNATURE,
    )

    # Then
    assert result is True


def test_verify_github_webhook_payload_returns_false_on_bad_signature() -> None:
    # When
    result = github_webhook_payload_is_valid(
        payload_body=WEBHOOK_PAYLOAD.encode("utf-8"),
        secret_token=WEBHOOK_SECRET,
        signature_header="sha1=757107ea0eb2509fc211221cce984b8a37570b6d7586c22c46f4379c8b043e18",
    )

    # Then
    assert result is False


def test_verify_github_webhook_payload_returns_false_on_no_signature_header() -> None:
    # When
    result = github_webhook_payload_is_valid(
        payload_body=WEBHOOK_PAYLOAD.encode("utf-8"),
        secret_token=WEBHOOK_SECRET,
        signature_header=None,
    )

    # Then
    assert result is False


def test_github_webhook_delete_installation(
    api_client: APIClient,
    github_configuration: GithubConfiguration,
) -> None:
    # Given
    settings.GITHUB_WEBHOOK_SECRET = WEBHOOK_SECRET
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


def test_github_webhook_with_non_existing_installation(
    api_client: APIClient,
    github_configuration: GithubConfiguration,
    mocker: MockerFixture,
) -> None:
    # Given
    settings.GITHUB_WEBHOOK_SECRET = WEBHOOK_SECRET
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


def test_github_webhook_without_installation_id(
    api_client: APIClient,
    github_configuration: GithubConfiguration,
    mocker: MockerFixture,
) -> None:
    # Given
    settings.GITHUB_WEBHOOK_SECRET = WEBHOOK_SECRET
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


def test_github_webhook_fails_on_signature_header_missing(
    github_configuration: GithubConfiguration,
) -> None:
    # Given
    settings.GITHUB_WEBHOOK_SECRET = WEBHOOK_SECRET
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


def test_github_webhook_fails_on_bad_signature_header_missing(
    github_configuration: GithubConfiguration,
) -> None:
    # Given
    settings.GITHUB_WEBHOOK_SECRET = WEBHOOK_SECRET
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


def test_github_webhook_bypass_event(
    github_configuration: GithubConfiguration,
) -> None:
    # Given
    settings.GITHUB_WEBHOOK_SECRET = WEBHOOK_SECRET
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
def test_cannot_fetch_pull_requests_when_github_request_call_failed(
    admin_client_new: APIClient,
    organisation: Organisation,
    github_configuration: GithubConfiguration,
    github_repository: GithubRepository,
    mocker,
) -> None:

    # Given
    data = {"repo_owner": "owner", "repo_name": "repo"}
    mock_generate_token = mocker.patch(
        "integrations.github.client.generate_token",
    )
    mock_generate_token.return_value = "mocked_token"
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
def test_cannot_fetch_pulls_when_the_github_response_was_invalid(
    admin_client_new: APIClient,
    organisation: Organisation,
    github_configuration: GithubConfiguration,
    github_repository: GithubRepository,
    mocker,
) -> None:
    # Given
    data = {"repo_owner": "owner", "repo_name": "repo"}
    mock_generate_token = mocker.patch(
        "integrations.github.client.generate_token",
    )
    mock_generate_token.return_value = "mocked_token"
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


def test_cannot_fetch_repositories_when_there_is_no_installation_id(
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
def test_fetch_github_repo_contributors(
    admin_client_new: APIClient,
    organisation: Organisation,
    github_configuration: GithubConfiguration,
    github_repository: GithubRepository,
    mocker: MockerFixture,
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

    mock_generate_token = mocker.patch(
        "integrations.github.client.generate_token",
    )
    mock_generate_token.return_value = "mocked_token"

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


def test_fetch_github_repo_contributors_with_invalid_query_params(
    admin_client_new: APIClient,
    organisation: Organisation,
    github_configuration: GithubConfiguration,
    github_repository: GithubRepository,
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


def test_github_api_call_error_handler_with_value_error(
    mocker: MockerFixture,
) -> None:
    # Given
    @github_api_call_error_handler()
    def test_view(request):
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
def test_send_the_invalid_number_page_or_page_size_param_returns_400(
    admin_client: APIClient,
    organisation: Organisation,
    github_configuration: GithubConfiguration,
    github_repository: GithubRepository,
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
def test_send_the_invalid_type_page_or_page_size_param_returns_400(
    admin_client: APIClient,
    organisation: Organisation,
    github_configuration: GithubConfiguration,
    github_repository: GithubRepository,
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
