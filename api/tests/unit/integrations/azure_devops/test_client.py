from integrations.azure_devops.client.types import AdoProject, AdoProjectsPage


def test_ado_project__shape__has_required_keys() -> None:
    # Given
    project: AdoProject = {
        "id": "00000000-0000-0000-0000-000000000000",
        "name": "Test",
        "url": "https://dev.azure.com/test-org/_apis/projects/...",
    }

    # When
    keys = set(project.keys())

    # Then
    assert keys == {"id", "name", "url"}


def test_ado_projects_page__shape__has_required_keys() -> None:
    # Given
    page: AdoProjectsPage = {"results": [], "continuation_token": None}

    # When
    keys = set(page.keys())

    # Then
    assert keys == {"results", "continuation_token"}
