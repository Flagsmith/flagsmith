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
