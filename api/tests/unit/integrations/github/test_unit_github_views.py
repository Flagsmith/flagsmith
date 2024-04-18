import pytest
from django.db import IntegrityError
from django.urls import reverse
from pytest_lazyfixture import lazy_fixture
from rest_framework import status
from rest_framework.test import APIClient

from integrations.github.models import GithubConfiguration, GithubRepository
from organisations.models import Organisation
from projects.models import Project


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_get_github_configuration(
    client: APIClient,
    organisation: Organisation,
) -> None:
    # Given
    url = reverse(
        "api-v1:organisations:integrations-github-list",
        kwargs={"organisation_pk": organisation.id},
    )
    # When
    response = client.get(url)
    # Then
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_create_github_configuration(
    client: APIClient,
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
    response = client.post(url, data)
    # Then
    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_delete_github_configuration(
    client: APIClient,
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
    response = client.delete(url)
    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_get_github_repository(
    client: APIClient,
    organisation: Organisation,
    github_configuration: GithubConfiguration,
):
    # Given
    url = reverse(
        "api-v1:organisations:repositories-list",
        args=[organisation.id, github_configuration.id],
    )
    # When
    response = client.get(url)
    # Then
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_create_github_repository(
    client: APIClient,
    organisation: Organisation,
    github_configuration: GithubConfiguration,
    project: Project,
) -> None:
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

    response = client.post(url, data)

    assert response.status_code == status.HTTP_201_CREATED
    assert GithubRepository.objects.filter(repository_owner="repositoryowner").exists()


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_cannot_create_github_repository_due_to_unique_constraint(
    client: APIClient,
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
    with pytest.raises(IntegrityError) as exc_info:
        response = client.post(url, data)

        # Then
        assert "duplicate key value violates unique constraint" in str(exc_info.value)
        assert "(5, 3, repositoryownertest, repositorynametest) already exists." in str(
            exc_info.value
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_github_delete_repository(
    client: APIClient,
    organisation: Organisation,
    github_configuration: GithubConfiguration,
    github_repository: GithubRepository,
) -> None:
    url = reverse(
        "api-v1:organisations:repositories-detail",
        args=[organisation.id, github_configuration.id, github_repository.id],
    )
    response = client.delete(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.fixture()
def edge_identity_dynamo_wrapper_mock(mocker):
    return mocker.patch(
        "edge_api.identities.models.EdgeIdentity.dynamo_wrapper",
    )


@pytest.fixture
def mock_generate_token(mocker):
    return mocker.patch(
        "integrations.github.client.generate_token",
    )


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


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
def test_fetch_pull_requests(
    client: APIClient,
    mock_generate_token,
    organisation: Organisation,
    github_configuration: GithubConfiguration,
    github_repository: GithubRepository,
    mocker,
):

    mock_generate_token.return_value = "mocked_token"
    github_request_mock = mocker.patch("requests.get", side_effect=mocked_requests_get)

    # mock_requests.get.return_value.json.return_value = {"data": "test"}

    url = reverse("api-v1:organisations:get-github-pulls", args=[organisation.id])
    data = {"repo_owner": "owner", "repo_name": "repo"}
    response = client.get(url, data=data)

    assert response.status_code == 200

    response_json = response.json()
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


def test_fetch_pull_requests_fails_with_status_400_when_integration_not_configured(
    admin_client,
    mock_generate_token,
    organisation,
):
    mock_generate_token.generate_token.return_value = "mocked_token"
    # mock_requests.get.return_value.json.return_value = {"data": "test"}

    url = reverse("api-v1:organisations:get-github-pulls", args=[organisation.id])
    response = admin_client.get(url)

    assert response.status_code == 400
