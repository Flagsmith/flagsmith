import responses
from pytest_structlog import StructuredLogCapture
from rest_framework import status
from rest_framework.test import APIClient

from integrations.azure_devops.models import AzureDevOpsConfiguration
from projects.models import Project


@responses.activate
def test_create_configuration__valid_data__persists_and_masks_token(
    admin_client_new: APIClient,
    project: Project,
    log: StructuredLogCapture,
) -> None:
    # Given
    responses.get(
        "https://dev.azure.com/test-org/_apis/projects",
        json={"value": [], "count": 0},
        status=200,
    )
    url = f"/api/v1/projects/{project.id}/integrations/azure-devops/"
    payload = {
        "organisation_url": "https://dev.azure.com/test-org",
        "personal_access_token": "ado-test-token",
    }

    # When
    response = admin_client_new.post(url, data=payload, format="json")

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["personal_access_token"] == "write-only"
    assert response.json()["labeling_enabled"] is False
    assert response.json()["tagging_enabled"] is False

    config = AzureDevOpsConfiguration.objects.get(project=project)
    assert config.organisation_url == "https://dev.azure.com/test-org"
    assert config.personal_access_token == "ado-test-token"

    assert log.events == [
        {
            "event": "configuration.created",
            "level": "info",
            "organisation__id": project.organisation_id,
            "project__id": project.id,
            "ado__organisation__url": "https://dev.azure.com/test-org",
        },
    ]


def test_create_configuration__already_exists__returns_400(
    admin_client_new: APIClient,
    project: Project,
    azure_devops_configuration: AzureDevOpsConfiguration,
) -> None:
    # Given
    url = f"/api/v1/projects/{project.id}/integrations/azure-devops/"
    payload = {
        "organisation_url": "https://dev.azure.com/other",
        "personal_access_token": "ado-other-token",
    }

    # When
    response = admin_client_new.post(url, data=payload, format="json")

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@responses.activate
def test_create_configuration__after_soft_delete__undeletes_existing_row(
    admin_client_new: APIClient,
    project: Project,
    azure_devops_configuration: AzureDevOpsConfiguration,
) -> None:
    # Given
    responses.get(
        "https://dev.azure.com/recreated/_apis/projects",
        json={"value": [], "count": 0},
        status=200,
    )
    original_pk = azure_devops_configuration.pk
    azure_devops_configuration.delete()
    url = f"/api/v1/projects/{project.id}/integrations/azure-devops/"
    payload = {
        "organisation_url": "https://dev.azure.com/recreated",
        "personal_access_token": "ado-recreated-token",
    }

    # When
    response = admin_client_new.post(url, data=payload, format="json")

    # Then
    assert response.status_code == status.HTTP_201_CREATED
    config = AzureDevOpsConfiguration.objects.get(project=project)
    assert config.pk == original_pk
    assert config.organisation_url == "https://dev.azure.com/recreated"
    assert config.personal_access_token == "ado-recreated-token"


def test_list_configuration__existing__returns_masked_representation(
    admin_client_new: APIClient,
    project: Project,
    azure_devops_configuration: AzureDevOpsConfiguration,
) -> None:
    # Given
    url = f"/api/v1/projects/{project.id}/integrations/azure-devops/"

    # When
    response = admin_client_new.get(url)

    # Then
    assert response.status_code == status.HTTP_200_OK
    rows = response.json()
    assert len(rows) == 1
    assert rows[0]["personal_access_token"] == "write-only"
    assert rows[0]["organisation_url"] == azure_devops_configuration.organisation_url


@responses.activate
def test_update_configuration__valid_data__persists_and_masks_token(
    admin_client_new: APIClient,
    project: Project,
    azure_devops_configuration: AzureDevOpsConfiguration,
    log: StructuredLogCapture,
) -> None:
    # Given
    responses.get(
        "https://dev.azure.com/updated/_apis/projects",
        json={"value": [], "count": 0},
        status=200,
    )
    detail_url = (
        f"/api/v1/projects/{project.id}/integrations/azure-devops/"
        f"{azure_devops_configuration.id}/"
    )
    payload = {
        "organisation_url": "https://dev.azure.com/updated",
        "personal_access_token": "ado-updated-token",
        "labeling_enabled": True,
        "tagging_enabled": True,
    }

    # When
    response = admin_client_new.put(detail_url, data=payload, format="json")

    # Then
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["personal_access_token"] == "write-only"

    azure_devops_configuration.refresh_from_db()
    assert (
        azure_devops_configuration.organisation_url == "https://dev.azure.com/updated"
    )
    assert azure_devops_configuration.personal_access_token == "ado-updated-token"
    assert azure_devops_configuration.labeling_enabled is True
    assert azure_devops_configuration.tagging_enabled is True

    assert log.events == [
        {
            "event": "configuration.updated",
            "level": "info",
            "organisation__id": project.organisation_id,
            "project__id": project.id,
            "ado__organisation__url": "https://dev.azure.com/updated",
        },
    ]


def test_delete_configuration__existing__soft_deletes_and_logs(
    admin_client_new: APIClient,
    project: Project,
    azure_devops_configuration: AzureDevOpsConfiguration,
    log: StructuredLogCapture,
) -> None:
    # Given
    detail_url = (
        f"/api/v1/projects/{project.id}/integrations/azure-devops/"
        f"{azure_devops_configuration.id}/"
    )

    # When
    response = admin_client_new.delete(detail_url)

    # Then
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert not AzureDevOpsConfiguration.objects.filter(project=project).exists()
    assert (
        AzureDevOpsConfiguration.objects.all_with_deleted()
        .filter(project=project)
        .exists()
    )

    assert log.events == [
        {
            "event": "configuration.deleted",
            "level": "info",
            "organisation__id": project.organisation_id,
            "project__id": project.id,
        },
    ]


def test_list_configuration__unauthenticated__returns_unauthorised(
    api_client: APIClient,
    project: Project,
) -> None:
    # Given
    url = f"/api/v1/projects/{project.id}/integrations/azure-devops/"

    # When
    response = api_client.get(url)

    # Then
    assert response.status_code in (
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    )


def test_create_configuration__non_admin__returns_403(
    staff_client: APIClient,
    project: Project,
) -> None:
    # Given
    url = f"/api/v1/projects/{project.id}/integrations/azure-devops/"
    payload = {
        "organisation_url": "https://dev.azure.com/test-org",
        "personal_access_token": "ado-test-token",
    }

    # When
    response = staff_client.post(url, data=payload, format="json")

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_delete_configuration__non_admin__returns_403(
    staff_client: APIClient,
    project: Project,
    azure_devops_configuration: AzureDevOpsConfiguration,
) -> None:
    # Given
    detail_url = (
        f"/api/v1/projects/{project.id}/integrations/azure-devops/"
        f"{azure_devops_configuration.id}/"
    )

    # When
    response = staff_client.delete(detail_url)

    # Then
    assert response.status_code == status.HTTP_403_FORBIDDEN


@responses.activate
def test_create_configuration__invalid_pat__returns_400(
    admin_client_new: APIClient,
    project: Project,
) -> None:
    # Given
    responses.get(
        "https://dev.azure.com/test-org/_apis/projects",
        json={},
        status=401,
    )
    url = f"/api/v1/projects/{project.id}/integrations/azure-devops/"
    payload = {
        "organisation_url": "https://dev.azure.com/test-org",
        "personal_access_token": "ado-bogus-token",
    }

    # When
    response = admin_client_new.post(url, data=payload, format="json")

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Azure DevOps rejected" in str(response.json())
    assert not AzureDevOpsConfiguration.objects.filter(project=project).exists()


@responses.activate
def test_update_configuration__placeholder_pat__skips_validation(
    admin_client_new: APIClient,
    project: Project,
    azure_devops_configuration: AzureDevOpsConfiguration,
) -> None:
    # Given — no ADO probe response registered; if validation runs, the test
    # will fail with a `responses.ConnectionError`.
    detail_url = (
        f"/api/v1/projects/{project.id}/integrations/azure-devops/"
        f"{azure_devops_configuration.id}/"
    )
    payload = {
        "organisation_url": azure_devops_configuration.organisation_url,
        "personal_access_token": "write-only",
        "labeling_enabled": True,
        "tagging_enabled": True,
    }
    original_pat = azure_devops_configuration.personal_access_token

    # When
    response = admin_client_new.put(detail_url, data=payload, format="json")

    # Then
    assert response.status_code == status.HTTP_200_OK
    azure_devops_configuration.refresh_from_db()
    assert azure_devops_configuration.personal_access_token == original_pat
    assert azure_devops_configuration.labeling_enabled is True
    assert azure_devops_configuration.tagging_enabled is True


@responses.activate
def test_create_configuration__ado_5xx__returns_400_with_retry_message(
    admin_client_new: APIClient,
    project: Project,
) -> None:
    # Given
    responses.get(
        "https://dev.azure.com/test-org/_apis/projects",
        json={},
        status=503,
    )
    url = f"/api/v1/projects/{project.id}/integrations/azure-devops/"
    payload = {
        "organisation_url": "https://dev.azure.com/test-org",
        "personal_access_token": "ado-test-token",
    }

    # When
    response = admin_client_new.post(url, data=payload, format="json")

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Azure DevOps could not be reached" in str(response.json())
    assert not AzureDevOpsConfiguration.objects.filter(project=project).exists()
