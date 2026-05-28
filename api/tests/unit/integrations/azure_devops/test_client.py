import base64

import pytest
import requests
import responses

from integrations.azure_devops.client import list_projects
from integrations.azure_devops.client.exceptions import (
    AzureDevOpsAuthError,
    AzureDevOpsNotFoundError,
)
from integrations.azure_devops.client.types import AdoProject, AdoProjectsPage

ORG_URL = "https://dev.azure.com/test-org"
PAT = "ado-test-pat"


def _expected_basic_auth_header() -> str:
    # ADO PAT auth: HTTP Basic with empty username and PAT as password.
    encoded = base64.b64encode(f":{PAT}".encode()).decode()
    return f"Basic {encoded}"


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


@responses.activate
def test_list_projects__valid_response__returns_typed_page() -> None:
    # Given
    responses.get(
        f"{ORG_URL}/_apis/projects",
        json={
            "value": [
                {
                    "id": "00000000-0000-0000-0000-000000000001",
                    "name": "Alpha",
                    "url": f"{ORG_URL}/_apis/projects/00000000-0000-0000-0000-000000000001",
                    "extra": "ignored",
                },
            ],
            "count": 1,
        },
        match=[
            responses.matchers.header_matcher(
                {"Authorization": _expected_basic_auth_header()}
            )
        ],
    )

    # When
    page = list_projects(organisation_url=ORG_URL, pat=PAT, top=1)

    # Then
    assert page["results"] == [
        {
            "id": "00000000-0000-0000-0000-000000000001",
            "name": "Alpha",
            "url": f"{ORG_URL}/_apis/projects/00000000-0000-0000-0000-000000000001",
        },
    ]
    assert page["continuation_token"] is None


@responses.activate
def test_list_projects__continuation_token_in_header__exposed_on_page() -> None:
    # Given
    responses.get(
        f"{ORG_URL}/_apis/projects",
        json={"value": [], "count": 0},
        headers={"x-ms-continuationtoken": "ct-abc"},
    )

    # When
    page = list_projects(organisation_url=ORG_URL, pat=PAT)

    # Then
    assert page["continuation_token"] == "ct-abc"


@responses.activate
def test_list_projects__401_response__raises_auth_error() -> None:
    # Given
    responses.get(f"{ORG_URL}/_apis/projects", json={}, status=401)

    # When
    def call_list() -> None:
        list_projects(organisation_url=ORG_URL, pat=PAT)

    # Then
    with pytest.raises(AzureDevOpsAuthError):
        call_list()


@responses.activate
def test_list_projects__403_response__raises_auth_error() -> None:
    # Given
    responses.get(f"{ORG_URL}/_apis/projects", json={}, status=403)

    # When
    def call_list() -> None:
        list_projects(organisation_url=ORG_URL, pat=PAT)

    # Then
    with pytest.raises(AzureDevOpsAuthError):
        call_list()


@responses.activate
def test_list_projects__404_response__raises_not_found_error() -> None:
    # Given
    responses.get(f"{ORG_URL}/_apis/projects", json={}, status=404)

    # When
    def call_list() -> None:
        list_projects(organisation_url=ORG_URL, pat=PAT)

    # Then
    with pytest.raises(AzureDevOpsNotFoundError):
        call_list()


@responses.activate
def test_list_projects__500_response__raises_requests_http_error() -> None:
    # Given
    responses.get(f"{ORG_URL}/_apis/projects", json={}, status=500)

    # When
    def call_list() -> None:
        list_projects(organisation_url=ORG_URL, pat=PAT)

    # Then — non-4xx server failures bubble up as the underlying requests error
    with pytest.raises(requests.HTTPError):
        call_list()


@responses.activate
def test_list_projects__trailing_slash_in_org_url__normalised_in_request() -> None:
    # Given
    responses.get(
        f"{ORG_URL}/_apis/projects",
        json={"value": [], "count": 0},
    )

    # When
    list_projects(organisation_url=f"{ORG_URL}/", pat=PAT)

    # Then — request lands on ORG_URL/_apis/projects (no double slash)
    # `responses.calls[0]` is typed as `Call | list[Call]`; in practice a single
    # index returns a `Call`. Same workaround as other tests in this codebase.
    assert responses.calls[0].request.url is not None  # type: ignore[union-attr]
    assert "//_apis" not in responses.calls[0].request.url  # type: ignore[union-attr]


@responses.activate
def test_list_projects__continuation_token_param__sent_in_request_query() -> None:
    # Given
    responses.get(
        f"{ORG_URL}/_apis/projects",
        json={"value": [], "count": 0},
        match=[
            responses.matchers.query_param_matcher(
                {"continuationToken": "ct-abc"},
                strict_match=False,
            )
        ],
    )

    # When
    list_projects(
        organisation_url=ORG_URL,
        pat=PAT,
        continuation_token="ct-abc",
    )

    # Then — request landed on the matched URL with the expected query param
    assert len(responses.calls) == 1


from integrations.azure_devops.client.types import (
    AdoPullRequest,
    AdoPullRequestsPage,
    AdoRepository,
    AdoWorkItem,
    AdoWorkItemsPage,
)


def test_ado_repository__shape__has_required_keys() -> None:
    # Given
    repo: AdoRepository = {
        "id": "00000000-0000-0000-0000-000000000001",
        "name": "my-repo",
        "default_branch": "refs/heads/main",
    }

    # When
    keys = set(repo.keys())

    # Then
    assert keys == {"id", "name", "default_branch"}


def test_ado_pull_request__shape__has_required_keys() -> None:
    # Given
    pr: AdoPullRequest = {
        "id": 42,
        "title": "Add feature X",
        "state": "active",
        "is_draft": False,
        "web_url": "https://dev.azure.com/test-org/proj/_git/repo/pullrequest/42",
        "repository_name": "repo",
    }

    # When
    keys = set(pr.keys())

    # Then
    assert keys == {"id", "title", "state", "is_draft", "web_url", "repository_name"}


def test_ado_pull_requests_page__shape__has_required_keys() -> None:
    # Given
    page: AdoPullRequestsPage = {"results": [], "continuation_token": None}

    # When
    keys = set(page.keys())

    # Then
    assert keys == {"results", "continuation_token"}


def test_ado_work_item__shape__has_required_keys() -> None:
    # Given
    work_item: AdoWorkItem = {
        "id": 100,
        "title": "Fix bug",
        "state": "Active",
        "work_item_type": "Bug",
        "web_url": "https://dev.azure.com/test-org/proj/_workitems/edit/100",
    }

    # When
    keys = set(work_item.keys())

    # Then
    assert keys == {"id", "title", "state", "work_item_type", "web_url"}


def test_ado_work_items_page__shape__has_required_keys() -> None:
    # Given
    page: AdoWorkItemsPage = {"results": [], "continuation_token": None}

    # When
    keys = set(page.keys())

    # Then
    assert keys == {"results", "continuation_token"}
