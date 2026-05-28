import base64

import pytest
import requests
import responses

from integrations.azure_devops.client import (
    add_pull_request_comment,
    add_work_item_comment,
    list_projects,
    list_pull_requests,
    list_repositories,
    list_work_items,
)
from integrations.azure_devops.client.exceptions import (
    AzureDevOpsAuthError,
    AzureDevOpsNotFoundError,
)
from integrations.azure_devops.client.types import (
    AdoProject,
    AdoProjectsPage,
    AdoPullRequest,
    AdoPullRequestsPage,
    AdoRepository,
    AdoWorkItem,
    AdoWorkItemsPage,
)

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


@responses.activate
def test_list_repositories__valid_response__returns_typed_list() -> None:
    # Given
    ado_project_id = "00000000-0000-0000-0000-0000000000aa"
    responses.get(
        f"{ORG_URL}/{ado_project_id}/_apis/git/repositories",
        json={
            "value": [
                {
                    "id": "00000000-0000-0000-0000-000000000bb1",
                    "name": "frontend",
                    "defaultBranch": "refs/heads/main",
                    "extra": "ignored",
                },
                {
                    "id": "00000000-0000-0000-0000-000000000bb2",
                    "name": "backend",
                    "defaultBranch": "refs/heads/develop",
                },
            ],
            "count": 2,
        },
    )

    # When
    repos = list_repositories(
        organisation_url=ORG_URL,
        pat=PAT,
        ado_project_id=ado_project_id,
    )

    # Then
    assert repos == [
        {
            "id": "00000000-0000-0000-0000-000000000bb1",
            "name": "frontend",
            "default_branch": "refs/heads/main",
        },
        {
            "id": "00000000-0000-0000-0000-000000000bb2",
            "name": "backend",
            "default_branch": "refs/heads/develop",
        },
    ]


@responses.activate
def test_list_repositories__missing_default_branch__defaults_to_empty_string() -> None:
    # Given
    ado_project_id = "00000000-0000-0000-0000-000000000aa1"
    responses.get(
        f"{ORG_URL}/{ado_project_id}/_apis/git/repositories",
        json={
            "value": [
                {
                    "id": "00000000-0000-0000-0000-000000000bb3",
                    "name": "empty-repo",
                },
            ],
            "count": 1,
        },
    )

    # When
    repos = list_repositories(
        organisation_url=ORG_URL,
        pat=PAT,
        ado_project_id=ado_project_id,
    )

    # Then — ADO omits `defaultBranch` for repos with no commits yet
    assert repos[0]["default_branch"] == ""


@responses.activate
def test_list_pull_requests__default_params__filters_state_active() -> None:
    # Given
    ado_project_id = "00000000-0000-0000-0000-0000000000aa"
    responses.get(
        f"{ORG_URL}/{ado_project_id}/_apis/git/pullrequests",
        json={
            "value": [
                {
                    "pullRequestId": 42,
                    "title": "Add feature X",
                    "status": "active",
                    "isDraft": False,
                    "repository": {"name": "frontend"},
                    "_links": {
                        "web": {
                            "href": "https://dev.azure.com/test-org/proj/_git/frontend/pullrequest/42"
                        }
                    },
                },
            ],
            "count": 1,
        },
        match=[
            responses.matchers.query_param_matcher(
                {"searchCriteria.status": "active"},
                strict_match=False,
            )
        ],
    )

    # When
    page = list_pull_requests(
        organisation_url=ORG_URL,
        pat=PAT,
        ado_project_id=ado_project_id,
    )

    # Then
    assert page["results"] == [
        {
            "id": 42,
            "title": "Add feature X",
            "state": "active",
            "is_draft": False,
            "web_url": "https://dev.azure.com/test-org/proj/_git/frontend/pullrequest/42",
            "repository_name": "frontend",
        },
    ]
    assert page["continuation_token"] is None


@responses.activate
def test_list_pull_requests__state_completed__sends_completed_in_query() -> None:
    # Given
    ado_project_id = "00000000-0000-0000-0000-0000000000aa"
    responses.get(
        f"{ORG_URL}/{ado_project_id}/_apis/git/pullrequests",
        json={"value": [], "count": 0},
        match=[
            responses.matchers.query_param_matcher(
                {"searchCriteria.status": "completed"},
                strict_match=False,
            )
        ],
    )

    # When
    list_pull_requests(
        organisation_url=ORG_URL,
        pat=PAT,
        ado_project_id=ado_project_id,
        state="completed",
    )

    # Then — matched URL implies the right query
    assert len(responses.calls) == 1


@responses.activate
def test_list_pull_requests__continuation_token_in_header__exposed_on_page() -> None:
    # Given
    ado_project_id = "00000000-0000-0000-0000-0000000000aa"
    responses.get(
        f"{ORG_URL}/{ado_project_id}/_apis/git/pullrequests",
        json={"value": [], "count": 0},
        headers={"x-ms-continuationtoken": "pr-next"},
    )

    # When
    page = list_pull_requests(
        organisation_url=ORG_URL,
        pat=PAT,
        ado_project_id=ado_project_id,
    )

    # Then
    assert page["continuation_token"] == "pr-next"


@responses.activate
def test_list_work_items__title_search_and_type__sends_wiql_and_hydrates() -> None:
    # Given
    ado_project_id = "00000000-0000-0000-0000-0000000000aa"
    expected_wiql_query = (
        "SELECT [System.Id] FROM WorkItems "
        "WHERE [System.TeamProject] = @project "
        "AND [System.State] = 'Active' "
        "AND [System.WorkItemType] = 'Bug' "
        "AND [System.Title] CONTAINS 'login' "
        "ORDER BY [System.ChangedDate] DESC"
    )
    responses.post(
        f"{ORG_URL}/{ado_project_id}/_apis/wit/wiql",
        json={
            "workItems": [{"id": 101}, {"id": 102}],
        },
        match=[
            responses.matchers.json_params_matcher({"query": expected_wiql_query}),
        ],
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
                },
                {
                    "id": 102,
                    "fields": {
                        "System.Title": "Login slow",
                        "System.State": "Active",
                        "System.WorkItemType": "Bug",
                    },
                    "_links": {
                        "html": {
                            "href": "https://dev.azure.com/test-org/proj/_workitems/edit/102"
                        }
                    },
                },
            ]
        },
        match=[
            responses.matchers.json_params_matcher(
                {
                    "ids": [101, 102],
                    "fields": [
                        "System.Id",
                        "System.Title",
                        "System.State",
                        "System.WorkItemType",
                    ],
                }
            ),
        ],
    )

    # When
    page = list_work_items(
        organisation_url=ORG_URL,
        pat=PAT,
        ado_project_id=ado_project_id,
        search_text="login",
        state="Active",
        work_item_type="Bug",
    )

    # Then
    assert page["results"] == [
        {
            "id": 101,
            "title": "Login broken",
            "state": "Active",
            "work_item_type": "Bug",
            "web_url": "https://dev.azure.com/test-org/proj/_workitems/edit/101",
        },
        {
            "id": 102,
            "title": "Login slow",
            "state": "Active",
            "work_item_type": "Bug",
            "web_url": "https://dev.azure.com/test-org/proj/_workitems/edit/102",
        },
    ]
    assert page["continuation_token"] is None


@responses.activate
def test_list_work_items__no_filters__produces_minimal_wiql() -> None:
    # Given
    ado_project_id = "00000000-0000-0000-0000-0000000000aa"
    expected_wiql_query = (
        "SELECT [System.Id] FROM WorkItems "
        "WHERE [System.TeamProject] = @project "
        "ORDER BY [System.ChangedDate] DESC"
    )
    responses.post(
        f"{ORG_URL}/{ado_project_id}/_apis/wit/wiql",
        json={"workItems": []},
        match=[
            responses.matchers.json_params_matcher({"query": expected_wiql_query}),
        ],
    )

    # When
    page = list_work_items(
        organisation_url=ORG_URL,
        pat=PAT,
        ado_project_id=ado_project_id,
    )

    # Then — empty WIQL means no second call
    assert page["results"] == []
    assert len(responses.calls) == 1


@responses.activate
def test_list_work_items__search_text_with_quote__is_escaped() -> None:
    # Given
    ado_project_id = "00000000-0000-0000-0000-0000000000aa"
    expected_wiql_query = (
        "SELECT [System.Id] FROM WorkItems "
        "WHERE [System.TeamProject] = @project "
        "AND [System.Title] CONTAINS 'O''Brien' "
        "ORDER BY [System.ChangedDate] DESC"
    )
    responses.post(
        f"{ORG_URL}/{ado_project_id}/_apis/wit/wiql",
        json={"workItems": []},
        match=[
            responses.matchers.json_params_matcher({"query": expected_wiql_query}),
        ],
    )

    # When
    list_work_items(
        organisation_url=ORG_URL,
        pat=PAT,
        ado_project_id=ado_project_id,
        search_text="O'Brien",
    )

    # Then
    assert len(responses.calls) == 1


@responses.activate
def test_list_work_items__pagination__slices_wiql_ids_by_top_and_returns_continuation() -> (
    None
):
    # Given — WIQL returns 5 IDs; we ask for top=2
    ado_project_id = "00000000-0000-0000-0000-0000000000aa"
    responses.post(
        f"{ORG_URL}/{ado_project_id}/_apis/wit/wiql",
        json={
            "workItems": [
                {"id": 200},
                {"id": 201},
                {"id": 202},
                {"id": 203},
                {"id": 204},
            ]
        },
    )
    responses.post(
        f"{ORG_URL}/_apis/wit/workitemsbatch",
        json={
            "value": [
                {
                    "id": 200,
                    "fields": {
                        "System.Title": "WI 200",
                        "System.State": "Active",
                        "System.WorkItemType": "Task",
                    },
                    "_links": {"html": {"href": "url-200"}},
                },
                {
                    "id": 201,
                    "fields": {
                        "System.Title": "WI 201",
                        "System.State": "Active",
                        "System.WorkItemType": "Task",
                    },
                    "_links": {"html": {"href": "url-201"}},
                },
            ]
        },
        match=[
            responses.matchers.json_params_matcher(
                {
                    "ids": [200, 201],
                    "fields": [
                        "System.Id",
                        "System.Title",
                        "System.State",
                        "System.WorkItemType",
                    ],
                }
            ),
        ],
    )

    # When
    page = list_work_items(
        organisation_url=ORG_URL,
        pat=PAT,
        ado_project_id=ado_project_id,
        top=2,
    )

    # Then — first two IDs hydrated; continuation_token reflects offset of next batch
    assert [r["id"] for r in page["results"]] == [200, 201]
    assert page["continuation_token"] == "2"


@responses.activate
def test_list_work_items__continuation_token__starts_from_offset() -> None:
    # Given — same WIQL set, paginating with continuation_token="2"
    ado_project_id = "00000000-0000-0000-0000-0000000000aa"
    responses.post(
        f"{ORG_URL}/{ado_project_id}/_apis/wit/wiql",
        json={
            "workItems": [
                {"id": 200},
                {"id": 201},
                {"id": 202},
                {"id": 203},
                {"id": 204},
            ]
        },
    )
    responses.post(
        f"{ORG_URL}/_apis/wit/workitemsbatch",
        json={
            "value": [
                {
                    "id": 202,
                    "fields": {
                        "System.Title": "WI 202",
                        "System.State": "Active",
                        "System.WorkItemType": "Task",
                    },
                    "_links": {"html": {"href": "url-202"}},
                },
                {
                    "id": 203,
                    "fields": {
                        "System.Title": "WI 203",
                        "System.State": "Active",
                        "System.WorkItemType": "Task",
                    },
                    "_links": {"html": {"href": "url-203"}},
                },
            ]
        },
        match=[
            responses.matchers.json_params_matcher(
                {
                    "ids": [202, 203],
                    "fields": [
                        "System.Id",
                        "System.Title",
                        "System.State",
                        "System.WorkItemType",
                    ],
                }
            ),
        ],
    )

    # When
    page = list_work_items(
        organisation_url=ORG_URL,
        pat=PAT,
        ado_project_id=ado_project_id,
        top=2,
        continuation_token="2",
    )

    # Then
    assert [r["id"] for r in page["results"]] == [202, 203]
    assert page["continuation_token"] == "4"


@responses.activate
def test_list_work_items__last_page__omits_continuation_token() -> None:
    # Given — only one item left; second batch returns it; no further pages
    ado_project_id = "00000000-0000-0000-0000-0000000000aa"
    responses.post(
        f"{ORG_URL}/{ado_project_id}/_apis/wit/wiql",
        json={"workItems": [{"id": 999}]},
    )
    responses.post(
        f"{ORG_URL}/_apis/wit/workitemsbatch",
        json={
            "value": [
                {
                    "id": 999,
                    "fields": {
                        "System.Title": "Final",
                        "System.State": "Closed",
                        "System.WorkItemType": "Task",
                    },
                    "_links": {"html": {"href": "url-999"}},
                },
            ]
        },
    )

    # When
    page = list_work_items(
        organisation_url=ORG_URL,
        pat=PAT,
        ado_project_id=ado_project_id,
        top=10,
    )

    # Then — single result, no more pages
    assert page["results"][0]["id"] == 999
    assert page["continuation_token"] is None


@responses.activate
def test_add_pull_request_comment__valid_call__posts_thread_with_comment() -> None:
    # Given
    responses.post(
        f"{ORG_URL}/proj/_apis/git/pullrequests/42/threads",
        json={"id": 1},
        match=[
            responses.matchers.json_params_matcher(
                {
                    "comments": [{"content": "Hello"}],
                    "status": 1,
                }
            ),
        ],
    )

    # When
    add_pull_request_comment(
        organisation_url=ORG_URL,
        pat=PAT,
        project="proj",
        pull_request_id=42,
        body="Hello",
    )

    # Then
    assert len(responses.calls) == 1


@responses.activate
def test_add_pull_request_comment__500_response__raises_http_error() -> None:
    # Given
    responses.post(
        f"{ORG_URL}/proj/_apis/git/pullrequests/42/threads",
        json={},
        status=500,
    )

    # When
    def call_post() -> None:
        add_pull_request_comment(
            organisation_url=ORG_URL,
            pat=PAT,
            project="proj",
            pull_request_id=42,
            body="x",
        )

    # Then
    with pytest.raises(requests.HTTPError):
        call_post()


@responses.activate
def test_add_work_item_comment__valid_call__posts_comment_text() -> None:
    # Given
    responses.post(
        f"{ORG_URL}/proj/_apis/wit/workItems/100/comments",
        json={"id": 1},
        match=[
            responses.matchers.json_params_matcher({"text": "Hello world"}),
        ],
    )

    # When
    add_work_item_comment(
        organisation_url=ORG_URL,
        pat=PAT,
        project="proj",
        work_item_id=100,
        body="Hello world",
    )

    # Then
    assert len(responses.calls) == 1


@responses.activate
def test_add_work_item_comment__500_response__raises_http_error() -> None:
    # Given
    responses.post(
        f"{ORG_URL}/proj/_apis/wit/workItems/100/comments",
        json={},
        status=500,
    )

    # When
    def call_post() -> None:
        add_work_item_comment(
            organisation_url=ORG_URL,
            pat=PAT,
            project="proj",
            work_item_id=100,
            body="x",
        )

    # Then
    with pytest.raises(requests.HTTPError):
        call_post()
