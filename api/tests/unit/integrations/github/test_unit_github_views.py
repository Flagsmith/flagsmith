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


# @pytest.mark.parametrize(
#     "client",
#     [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
# )
# def test_github_delete_repository(
#     client: APIClient,
#     organisation: Organisation,
#     github_configuration: GithubConfiguration,
#     github_repository: GithubRepository,
# ) -> None:
#     url = reverse(
#         "api-v1:organisations:repositories-detail",
#         args=[organisation.id, github_configuration.id, github_repository.id],
#     )
#     response = client.delete(url)
#     assert response.status_code == status.HTTP_204_NO_CONTENT
