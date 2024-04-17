from unittest.mock import patch

import pytest
from django.conf import settings
from django.db import IntegrityError
from django.urls import reverse
from pytest_lazyfixture import lazy_fixture
from rest_framework import status
from rest_framework.test import APIClient

from integrations.github.client import generate_token
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


@pytest.mark.parametrize(
    "client",
    [lazy_fixture("admin_master_api_key_client"), lazy_fixture("admin_client")],
)
@pytest.mark.django_db
def test_fetch_pull_requests(
    mocker,
    admin_client: APIClient,
    organisation: Organisation,
    github_configuration: GithubConfiguration,
    github_repository: GithubRepository,
):

    class MockResponse:
        def __init__(self, status_code, json_data=None):
            self.status_code = status_code
            self.json_data = json_data

        def json(self):
            return self.json_data

    mocked_pem_content = """-----BEGIN CERTIFICATE-----
        MIICUTCCAfugAwIBAgIBADANBgkqhkiG9w0BAQQFADBXMQswCQYDVQQGEwJDTjEL
        MAkGA1UECBMCUE4xCzAJBgNVBAcTAkNOMQswCQYDVQQKEwJPTjELMAkGA1UECxMC
        VU4xFDASBgNVBAMTC0hlcm9uZyBZYW5nMB4XDTA1MDcxNTIxMTk0N1oXDTA1MDgx
        NDIxMTk0N1owVzELMAkGA1UEBhMCQ04xCzAJBgNVBAgTAlBOMQswCQYDVQQHEwJD
        TjELMAkGA1UEChMCT04xCzAJBgNVBAsTAlVOMRQwEgYDVQQDEwtIZXJvbmcgWWFu
        ZzBcMA0GCSqGSIb3DQEBAQUAA0sAMEgCQQCp5hnG7ogBhtlynpOS21cBewKE/B7j
        V14qeyslnr26xZUsSVko36ZnhiaO/zbMOoRcKK9vEcgMtcLFuQTWDl3RAgMBAAGj
        gbEwga4wHQYDVR0OBBYEFFXI70krXeQDxZgbaCQoR4jUDncEMH8GA1UdIwR4MHaA
        FFXI70krXeQDxZgbaCQoR4jUDncEoVukWTBXMQswCQYDVQQGEwJDTjELMAkGA1UE
        CBMCUE4xCzAJBgNVBAcTAkNOMQswCQYDVQQKEwJPTjELMAkGA1UECxMCVU4xFDAS
        BgNVBAMTC0hlcm9uZyBZYW5nggEAMAwGA1UdEwQFMAMBAf8wDQYJKoZIhvcNAQEE
        BQADQQA/ugzBrjjK9jcWnDVfGHlk3icNRq0oV7Ri32z/+HQX67aRfgZu7KWdI+Ju
        Wm7DCfrPNGVwFWUQOmsPue9rZBgO
    -----END CERTIFICATE-----"""

    settings.GITHUB_PEM = mocked_pem_content

    mocker.patch(
        "integrations.github.client.generate_token", return_value="TOKEN_DE_PRUEBA"
    )

    mocker.patch(
        "integrations.github.views.requests.get",
        return_value=MockResponse(status_code=200, json_data={"results": []}),
    )

    url = reverse("api-v1:organisations:get-github-pulls", args=[organisation.id])
    response = admin_client.get(url)

    assert response.status_code == 200

    assert "results" in response.data


@patch("github.Auth.AppAuth")
def test_generate_token(mocked_AppAuth):
    mocked_auth_instance = mocked_AppAuth.return_value
    mocked_auth_instance.get_installation_auth.return_value.token = "fake_token"

    installation_id = "123456"
    app_id = 789
    token = generate_token(installation_id, app_id)
    assert token == "fake_token"
