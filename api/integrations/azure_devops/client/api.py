from typing import Any

import requests

from integrations.azure_devops.client.exceptions import (
    AzureDevOpsAuthError,
    AzureDevOpsNotFoundError,
)
from integrations.azure_devops.client.types import AdoProject, AdoProjectsPage
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
    query: dict[str, Any] = {"api-version": AZURE_DEVOPS_API_VERSION}
    if params:
        query.update(params)
    response = requests.request(
        method,
        f"{base}/_apis/{path}",
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
