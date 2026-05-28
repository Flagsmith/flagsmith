import responses
from rest_framework import status
from rest_framework.test import APIClient

from integrations.azure_devops.models import AzureDevOpsConfiguration
from projects.models import Project

ORG_URL = "https://dev.azure.com/test-org"
ADO_PROJECT_ID = "00000000-0000-0000-0000-0000000000aa"


@responses.activate
def test_browse_projects__valid__returns_results_and_next_url(
    admin_client_new: APIClient,
    project: Project,
    azure_devops_configuration: AzureDevOpsConfiguration,
) -> None:
    # Given
    responses.get(
        f"{ORG_URL}/_apis/projects",
        json={
            "value": [
                {"id": ADO_PROJECT_ID, "name": "Proj", "url": "ado-url"},
            ],
            "count": 1,
        },
        headers={"x-ms-continuationtoken": "ct-next"},
    )

    # When
    response = admin_client_new.get(
        f"/api/v1/projects/{project.id}/azure-devops/projects/"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["results"] == [{"id": ADO_PROJECT_ID, "name": "Proj", "url": "ado-url"}]
    assert "continuation_token=ct-next" in body["next"]


@responses.activate
def test_browse_projects__no_configuration__returns_400(
    admin_client_new: APIClient,
    project: Project,
) -> None:
    # Given — no AzureDevOpsConfiguration for this project

    # When
    response = admin_client_new.get(
        f"/api/v1/projects/{project.id}/azure-devops/projects/"
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@responses.activate
def test_browse_projects__ado_unreachable__returns_503(
    admin_client_new: APIClient,
    project: Project,
    azure_devops_configuration: AzureDevOpsConfiguration,
) -> None:
    # Given
    responses.get(f"{ORG_URL}/_apis/projects", json={}, status=500)

    # When
    response = admin_client_new.get(
        f"/api/v1/projects/{project.id}/azure-devops/projects/"
    )

    # Then
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE


@responses.activate
def test_browse_repositories__valid__returns_typed_list(
    admin_client_new: APIClient,
    project: Project,
    azure_devops_configuration: AzureDevOpsConfiguration,
) -> None:
    # Given
    responses.get(
        f"{ORG_URL}/{ADO_PROJECT_ID}/_apis/git/repositories",
        json={
            "value": [
                {
                    "id": "00000000-0000-0000-0000-000000000bb1",
                    "name": "frontend",
                    "defaultBranch": "refs/heads/main",
                }
            ],
            "count": 1,
        },
    )

    # When
    response = admin_client_new.get(
        f"/api/v1/projects/{project.id}/azure-devops/repositories/"
        f"?ado_project_id={ADO_PROJECT_ID}"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["results"] == [
        {
            "id": "00000000-0000-0000-0000-000000000bb1",
            "name": "frontend",
            "default_branch": "refs/heads/main",
        }
    ]


def test_browse_repositories__missing_ado_project_id__returns_400(
    admin_client_new: APIClient,
    project: Project,
    azure_devops_configuration: AzureDevOpsConfiguration,
) -> None:
    # Given

    # When
    response = admin_client_new.get(
        f"/api/v1/projects/{project.id}/azure-devops/repositories/"
    )

    # Then
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@responses.activate
def test_browse_pull_requests__default_state__returns_active_prs(
    admin_client_new: APIClient,
    project: Project,
    azure_devops_configuration: AzureDevOpsConfiguration,
) -> None:
    # Given
    responses.get(
        f"{ORG_URL}/{ADO_PROJECT_ID}/_apis/git/pullrequests",
        json={
            "value": [
                {
                    "pullRequestId": 42,
                    "title": "Add X",
                    "status": "active",
                    "isDraft": False,
                    "repository": {"name": "frontend"},
                    "_links": {
                        "web": {
                            "href": "https://dev.azure.com/test-org/proj/_git/frontend/pullrequest/42"
                        }
                    },
                }
            ],
            "count": 1,
        },
    )

    # When
    response = admin_client_new.get(
        f"/api/v1/projects/{project.id}/azure-devops/pull-requests/"
        f"?ado_project_id={ADO_PROJECT_ID}"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["results"][0]["id"] == 42


@responses.activate
def test_browse_work_items__title_search__returns_hydrated_items(
    admin_client_new: APIClient,
    project: Project,
    azure_devops_configuration: AzureDevOpsConfiguration,
) -> None:
    # Given
    responses.post(
        f"{ORG_URL}/{ADO_PROJECT_ID}/_apis/wit/wiql",
        json={"workItems": [{"id": 101}]},
    )
    responses.post(
        f"{ORG_URL}/_apis/wit/workitemsbatch",
        json={
            "value": [
                {
                    "id": 101,
                    "fields": {
                        "System.Title": "Login broken",
                        "System.State": "Active",
                        "System.WorkItemType": "Bug",
                    },
                    "_links": {
                        "html": {
                            "href": "https://dev.azure.com/test-org/proj/_workitems/edit/101"
                        }
                    },
                }
            ]
        },
    )

    # When
    response = admin_client_new.get(
        f"/api/v1/projects/{project.id}/azure-devops/work-items/"
        f"?ado_project_id={ADO_PROJECT_ID}&search_text=login&state=Active&work_item_type=Bug"
    )

    # Then
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["results"][0]["id"] == 101


def test_browse_projects__unauthenticated__returns_unauthorised(
    api_client: APIClient,
    project: Project,
) -> None:
    # Given

    # When
    response = api_client.get(f"/api/v1/projects/{project.id}/azure-devops/projects/")

    # Then
    assert response.status_code in (
        status.HTTP_401_UNAUTHORIZED,
        status.HTTP_403_FORBIDDEN,
    )


@responses.activate
def test_browse_projects__ado_auth_failure__returns_502(
    admin_client_new: APIClient,
    project: Project,
    azure_devops_configuration: AzureDevOpsConfiguration,
) -> None:
    # Given
    responses.get(f"{ORG_URL}/_apis/projects", json={}, status=401)

    # When
    response = admin_client_new.get(
        f"/api/v1/projects/{project.id}/azure-devops/projects/"
    )

    # Then
    assert response.status_code == status.HTTP_502_BAD_GATEWAY
    assert "rejected the credentials" in str(response.json())


@responses.activate
def test_browse_repositories__unknown_ado_project_id__returns_404(
    admin_client_new: APIClient,
    project: Project,
    azure_devops_configuration: AzureDevOpsConfiguration,
) -> None:
    # Given
    bogus_project_id = "00000000-0000-0000-0000-000000000bad"
    responses.get(
        f"{ORG_URL}/{bogus_project_id}/_apis/git/repositories",
        json={},
        status=404,
    )

    # When
    response = admin_client_new.get(
        f"/api/v1/projects/{project.id}/azure-devops/repositories/"
        f"?ado_project_id={bogus_project_id}"
    )

    # Then
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "could not find" in str(response.json())
