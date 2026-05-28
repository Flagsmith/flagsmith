from typing import Any

import requests

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
from integrations.azure_devops.constants import (
    AZURE_DEVOPS_API_VERSION,
    AZURE_DEVOPS_CLIENT_TIMEOUT_SECONDS,
)


def _ado_request(
    method: str,
    organisation_url: str,
    pat: str,
    *,
    path: str,
    params: dict[str, Any] | None = None,
    json_body: dict[str, Any] | None = None,
) -> requests.Response:
    base = organisation_url.rstrip("/")
    # `path` may be either a bare segment ("projects") or already contain
    # "_apis/" (for project-scoped endpoints like
    # "{ado_project_id}/_apis/git/..."). Honour both.
    if "_apis/" in path:
        url = f"{base}/{path}"
    else:
        url = f"{base}/_apis/{path}"
    query: dict[str, Any] = {"api-version": AZURE_DEVOPS_API_VERSION}
    if params:
        query.update(params)
    response = requests.request(
        method,
        url,
        auth=("", pat),
        params=query,
        json=json_body,
        timeout=AZURE_DEVOPS_CLIENT_TIMEOUT_SECONDS,
    )
    if response.status_code in (401, 403):
        raise AzureDevOpsAuthError(
            f"Azure DevOps rejected credentials ({response.status_code})"
        )
    if response.status_code == 404:
        raise AzureDevOpsNotFoundError(
            f"Azure DevOps reported the resource was not found ({response.status_code})"
        )
    response.raise_for_status()
    return response


def list_projects(
    *,
    organisation_url: str,
    pat: str,
    top: int | None = None,
    continuation_token: str | None = None,
) -> AdoProjectsPage:
    params: dict[str, Any] = {}
    if top is not None:
        params["$top"] = top
    if continuation_token is not None:
        params["continuationToken"] = continuation_token

    response = _ado_request(
        "GET",
        organisation_url,
        pat,
        path="projects",
        params=params,
    )
    payload = response.json()
    results: list[AdoProject] = [
        AdoProject(id=p["id"], name=p["name"], url=p["url"])
        for p in payload.get("value", [])
    ]
    next_token = response.headers.get("x-ms-continuationtoken")
    return AdoProjectsPage(results=results, continuation_token=next_token)


def list_repositories(
    *,
    organisation_url: str,
    pat: str,
    ado_project_id: str,
) -> list[AdoRepository]:
    response = _ado_request(
        "GET",
        organisation_url,
        pat,
        path=f"{ado_project_id}/_apis/git/repositories",
    )
    payload = response.json()
    return [
        AdoRepository(
            id=item["id"],
            name=item["name"],
            default_branch=item.get("defaultBranch", ""),
        )
        for item in payload.get("value", [])
    ]


def list_pull_requests(
    *,
    organisation_url: str,
    pat: str,
    ado_project_id: str,
    state: str = "active",
    top: int | None = None,
    continuation_token: str | None = None,
) -> AdoPullRequestsPage:
    params: dict[str, Any] = {"searchCriteria.status": state}
    if top is not None:
        params["$top"] = top
    if continuation_token is not None:
        params["continuationToken"] = continuation_token

    response = _ado_request(
        "GET",
        organisation_url,
        pat,
        path=f"{ado_project_id}/_apis/git/pullrequests",
        params=params,
    )
    payload = response.json()
    results: list[AdoPullRequest] = [
        AdoPullRequest(
            id=item["pullRequestId"],
            title=item["title"],
            state=item["status"],
            is_draft=item.get("isDraft", False),
            web_url=item.get("_links", {}).get("web", {}).get("href", ""),
            repository_name=item.get("repository", {}).get("name", ""),
        )
        for item in payload.get("value", [])
    ]
    next_token = response.headers.get("x-ms-continuationtoken")
    return AdoPullRequestsPage(results=results, continuation_token=next_token)


_WORK_ITEM_FIELDS = [
    "System.Id",
    "System.Title",
    "System.State",
    "System.WorkItemType",
]


def _escape_wiql_string(value: str) -> str:
    # WIQL escapes single quotes by doubling them. There is no other
    # escape character. We control the column names; only user-supplied
    # values need this.
    return value.replace("'", "''")


def _wiql_query_for_work_items(
    *,
    search_text: str | None,
    state: str | None,
    work_item_type: str | None,
) -> str:
    clauses = ["[System.TeamProject] = @project"]
    if state:
        clauses.append(f"[System.State] = '{_escape_wiql_string(state)}'")
    if work_item_type:
        clauses.append(
            f"[System.WorkItemType] = '{_escape_wiql_string(work_item_type)}'"
        )
    if search_text:
        clauses.append(f"[System.Title] CONTAINS '{_escape_wiql_string(search_text)}'")
    where = " AND ".join(clauses)
    return (
        "SELECT [System.Id] FROM WorkItems "
        f"WHERE {where} "
        "ORDER BY [System.ChangedDate] DESC"
    )


def list_work_items(
    *,
    organisation_url: str,
    pat: str,
    ado_project_id: str,
    search_text: str | None = None,
    state: str | None = None,
    work_item_type: str | None = None,
    top: int = 100,
    continuation_token: str | None = None,
) -> AdoWorkItemsPage:
    """List ADO work items in a project, filterable by title text, state,
    and work-item type. Implemented as a WIQL query for the IDs followed
    by a batch fetch for the rows we want to display.

    Pagination is offset-based on the WIQL ID list (ADO returns up to
    20,000 IDs in one WIQL response per the docs). ``continuation_token``
    encodes the offset into the WIQL ID list as a string integer; the
    response's ``continuation_token`` is the offset to ask for next, or
    ``None`` if no further pages remain.
    """
    query = _wiql_query_for_work_items(
        search_text=search_text,
        state=state,
        work_item_type=work_item_type,
    )
    wiql_response = _ado_request(
        "POST",
        organisation_url,
        pat,
        path=f"{ado_project_id}/_apis/wit/wiql",
        json_body={"query": query},
    )
    wiql_payload = wiql_response.json()
    all_ids: list[int] = [item["id"] for item in wiql_payload.get("workItems", [])]
    if not all_ids:
        return AdoWorkItemsPage(results=[], continuation_token=None)

    offset = int(continuation_token) if continuation_token is not None else 0
    end = offset + top
    page_ids = all_ids[offset:end]
    if not page_ids:
        return AdoWorkItemsPage(results=[], continuation_token=None)

    batch_response = _ado_request(
        "POST",
        organisation_url,
        pat,
        path="wit/workitemsbatch",
        json_body={"ids": page_ids, "fields": _WORK_ITEM_FIELDS},
    )
    batch_payload = batch_response.json()
    results: list[AdoWorkItem] = [
        AdoWorkItem(
            id=item["id"],
            title=item.get("fields", {}).get("System.Title", ""),
            state=item.get("fields", {}).get("System.State", ""),
            work_item_type=item.get("fields", {}).get("System.WorkItemType", ""),
            web_url=item.get("_links", {}).get("html", {}).get("href", ""),
        )
        for item in batch_payload.get("value", [])
    ]
    next_token = str(end) if end < len(all_ids) else None
    return AdoWorkItemsPage(results=results, continuation_token=next_token)


def add_pull_request_comment(
    *,
    organisation_url: str,
    pat: str,
    project: str,
    pull_request_id: int,
    body: str,
) -> None:
    """Post a single-comment thread on an Azure DevOps pull request via
    its project-scoped threads endpoint.

    ``project`` is the ADO project name from the resource URL; the
    project-scoped form sidesteps needing the repository GUID. ``status: 1``
    is the ADO enum value for "Active".
    """
    _ado_request(
        "POST",
        organisation_url,
        pat,
        path=f"{project}/_apis/git/pullrequests/{pull_request_id}/threads",
        json_body={
            "comments": [{"content": body}],
            "status": 1,
        },
    )


def add_work_item_comment(
    *,
    organisation_url: str,
    pat: str,
    project: str,
    work_item_id: int,
    body: str,
) -> None:
    """Post a comment on an Azure DevOps work item via the modern Comments
    API.
    """
    _ado_request(
        "POST",
        organisation_url,
        pat,
        path=f"{project}/_apis/wit/workItems/{work_item_id}/comments",
        json_body={"text": body},
    )
