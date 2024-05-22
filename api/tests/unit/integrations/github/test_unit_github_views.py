import json

import pytest
from django.conf import settings
from django.urls import reverse
from pytest_lazyfixture import lazy_fixture
from pytest_mock import MockerFixture
from rest_framework import status
from rest_framework.test import APIClient

from features.feature_external_resources.models import FeatureExternalResource
from integrations.github.models import GithubConfiguration, GithubRepository
from integrations.github.views import github_webhook_payload_is_valid
from organisations.models import Organisation
from projects.models import Project

WEBHOOK_PAYLOAD = json.dumps({"installation": {"id": 1234567}, "action": "deleted"})
WEBHOOK_SIGNATURE = "sha1=57a1426e19cdab55dd6d0c191743e2958e50ccaa"
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


def test_delete_github_configuration(
    admin_client_new: APIClient,
    organisation: Organisation,
    github_configuration: GithubConfiguration,
    github_repository: GithubRepository,
) -> None:
    # Given
    url = reverse(
        "api-v1:organisations:integrations-github-detail",
        args=[
            organisation.id,
            github_configuration.id,
        ],
    )
    # When
    response = admin_client_new.delete(url)
    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT


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
    feature_external_resource: FeatureExternalResource,
    github_configuration: GithubConfiguration,
    github_repository: GithubRepository,
    mocker: MockerFixture,
) -> None:
    # Given
    mock_generate_token = mocker.patch(
        "integrations.github.github.generate_token",
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


def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def raise_for_status(self) -> None:
            pass

        def json(self):
            return self.json_data

    return MockResponse(json_data={"data": "data"}, status_code=200)


def test_fetch_pull_requests(
    admin_client_new: APIClient,
    organisation: Organisation,
    github_configuration: GithubConfiguration,
    github_repository: GithubRepository,
    mocker,
) -> None:

    # Given
    mock_generate_token = mocker.patch(
        "integrations.github.views.generate_token",
    )
    mock_generate_token.return_value = "mocked_token"
    github_request_mock = mocker.patch("requests.get", side_effect=mocked_requests_get)

    url = reverse("api-v1:organisations:get-github-pulls", args=[organisation.id])
    data = {"repo_owner": "owner", "repo_name": "repo"}

    # When
    response = admin_client_new.get(url, data=data)
    response_json = response.json()

    # Then
    assert response.status_code == 200
    assert "data" in response_json

    github_request_mock.assert_called_with(
        "https://api.github.com/repos/owner/repo/pulls",
        headers={
            "X-GitHub-Api-Version": "2022-11-28",
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "Bearer mocked_token",
        },
        timeout=10,
    )


def test_fetch_issue(
    admin_client_new: APIClient,
    organisation: Organisation,
    github_configuration: GithubConfiguration,
    github_repository: GithubRepository,
    mocker,
) -> None:
    # Given
    mock_generate_token = mocker.patch(
        "integrations.github.views.generate_token",
    )
    mock_generate_token.return_value = "mocked_token"
    github_request_mock = mocker.patch("requests.get", side_effect=mocked_requests_get)
    url = reverse("api-v1:organisations:get-github-issues", args=[organisation.id])
    data = {"repo_owner": "owner", "repo_name": "repo"}
    # When
    response = admin_client_new.get(url, data=data)

    # Then
    assert response.status_code == 200
    response_json = response.json()
    assert "data" in response_json

    github_request_mock.assert_called_with(
        "https://api.github.com/repos/owner/repo/issues",
        headers={
            "X-GitHub-Api-Version": "2022-11-28",
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "Bearer mocked_token",
        },
        timeout=10,
    )


def test_fetch_repositories(
    admin_client_new: APIClient,
    organisation: Organisation,
    github_configuration: GithubConfiguration,
    github_repository: GithubRepository,
    mocker,
) -> None:
    # Given
    mock_generate_token = mocker.patch(
        "integrations.github.views.generate_token",
    )
    mock_generate_token.return_value = "mocked_token"
    github_request_mock = mocker.patch("requests.get", side_effect=mocked_requests_get)
    url = reverse(
        "api-v1:organisations:get-github-installation-repos", args=[organisation.id]
    )
    # When
    response = admin_client_new.get(url)

    # Then
    assert response.status_code == 200
    response_json = response.json()
    assert "data" in response_json

    github_request_mock.assert_called_with(
        "https://api.github.com/installation/repositories",
        headers={
            "X-GitHub-Api-Version": "2022-11-28",
            "Accept": "application/vnd.github.v3+json",
            "Authorization": "Bearer mocked_token",
        },
        timeout=10,
    )


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
        "integrations.github.views.generate_token",
    )
    mock_generate_token.generate_token.return_value = "mocked_token"
    # When
    url = reverse(reverse_url, args=[organisation.id])
    response = client.get(url)

    # Then
    assert response.status_code == 400


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
        "integrations.github.views.generate_token",
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
        HTTP_X_GITHUB_EVENT="installation",
    )

    # Then
    assert response.status_code == 200
    assert not GithubConfiguration.objects.filter(installation_id=1234567).exists()


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
    assert response.status_code == 400
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
    assert response.status_code == 400
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
    assert response.status_code == 200
    assert GithubConfiguration.objects.filter(installation_id=1234567).exists()
