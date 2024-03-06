from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from integrations.github.models import GithubConfiguration, GithubRepository
from organisations.models import Organisation
from projects.models import Project


def test_get_github_configuration(
    admin_client: APIClient,
    organisation: Organisation,
) -> None:
    # Given
    url = reverse(
        "api-v1:organisations:integrations-github-list",
        kwargs={"organisation_pk": organisation.id},
    )
    # When
    response = admin_client.get(url)
    # Then
    assert response.status_code == status.HTTP_200_OK


def test_create_github_configuration(
    admin_client: APIClient,
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
    response = admin_client.post(url, data)
    # Then
    assert response.status_code == status.HTTP_201_CREATED


def test_delete_github_configuration(
    admin_client: APIClient,
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
    response = admin_client.delete(url)
    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_get_github_repository(
    admin_client: APIClient,
    organisation: Organisation,
    github_configuration: GithubConfiguration,
):
    # Given
    url = reverse(
        "api-v1:organisations:repositories-list",
        args=[organisation.id, github_configuration.id],
    )
    # When
    response = admin_client.get(url)
    # Then
    assert response.status_code == status.HTTP_200_OK


def test_create_github_repository(
    admin_client: APIClient,
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

    response = admin_client.post(url, data)

    assert response.status_code == status.HTTP_201_CREATED
    assert GithubRepository.objects.filter(repository_owner="repositoryowner").exists()


def test_github_delete_repository(
    admin_client: APIClient,
    organisation: Organisation,
    github_configuration: GithubConfiguration,
    github_repository: GithubRepository,
) -> None:
    url = reverse(
        "api-v1:organisations:repositories-detail",
        args=[organisation.id, github_configuration.id, github_repository.id],
    )
    response = admin_client.delete(url)
    assert response.status_code == status.HTTP_204_NO_CONTENT
