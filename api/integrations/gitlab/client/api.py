from collections.abc import Mapping
from typing import Any, Literal
from urllib.parse import quote

import requests

from integrations.gitlab.client.types import (
    GitLabIssue,
    GitLabMergeRequest,
    GitLabPage,
    GitLabProject,
    GitLabProjectHook,
    T,
)
from integrations.gitlab.constants import (
    GITLAB_CLIENT_TIMEOUT_SECONDS,
    GITLAB_FLAGSMITH_LABEL,
    GITLAB_FLAGSMITH_LABEL_COLOUR,
    GITLAB_FLAGSMITH_LABEL_DESCRIPTION,
)

GitLabResourceKind = Literal["issues", "merge_requests"]


def _get_from_gitlab_api(
    instance_url: str,
    access_token: str,
    *,
    path: str,
    params: dict[str, Any] | None = None,
) -> requests.Response:
    response = requests.get(
        f"{instance_url}/api/v4/{path}",
        headers={"PRIVATE-TOKEN": access_token},
        params=params,
        timeout=GITLAB_CLIENT_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return response


def _gitlab_page(
    results: list[T],
    headers: Mapping[str, str],
) -> GitLabPage[T]:
    return {
        "results": results,
        "current_page": int(headers.get("x-page", "1")),
        "total_pages": int(headers.get("x-total-pages", "1")),
        "total_count": int(headers.get("x-total", str(len(results)))),
    }


def fetch_gitlab_projects(
    instance_url: str,
    access_token: str,
    *,
    page: int,
    page_size: int,
) -> GitLabPage[GitLabProject]:
    response = _get_from_gitlab_api(
        instance_url,
        access_token,
        path="projects",
        params={
            "membership": "true",
            "per_page": str(page_size),
            "page": str(page),
        },
    )

    results: list[GitLabProject] = [
        GitLabProject(
            id=p["id"],
            name=p["name"],
            path_with_namespace=p["path_with_namespace"],
        )
        for p in response.json()
    ]
    return _gitlab_page(results, response.headers)


def search_gitlab_issues(
    instance_url: str,
    access_token: str,
    *,
    gitlab_project_id: int,
    page: int,
    page_size: int,
    search_text: str | None = None,
    state: str | None = "opened",
) -> GitLabPage[GitLabIssue]:
    query: dict[str, str | int] = {
        "per_page": page_size,
        "page": page,
    }
    if search_text:
        query["search"] = search_text
    if state:
        query["state"] = state

    response = _get_from_gitlab_api(
        instance_url,
        access_token,
        path=f"projects/{gitlab_project_id}/issues",
        params=query,
    )

    results: list[GitLabIssue] = [
        {
            "web_url": item["web_url"],
            "id": item["id"],
            "title": item["title"],
            "iid": item["iid"],
            "state": item["state"],
        }
        for item in response.json()
    ]
    return _gitlab_page(results, response.headers)


def search_gitlab_merge_requests(
    instance_url: str,
    access_token: str,
    *,
    gitlab_project_id: int,
    page: int,
    page_size: int,
    search_text: str | None = None,
    state: str | None = "opened",
) -> GitLabPage[GitLabMergeRequest]:
    query: dict[str, str | int] = {
        "per_page": page_size,
        "page": page,
    }
    if search_text:
        query["search"] = search_text
    if state:
        query["state"] = state

    response = _get_from_gitlab_api(
        instance_url,
        access_token,
        path=f"projects/{gitlab_project_id}/merge_requests",
        params=query,
    )

    results: list[GitLabMergeRequest] = [
        {
            "web_url": item["web_url"],
            "id": item["id"],
            "title": item["title"],
            "iid": item["iid"],
            "state": item["state"],
            "merged": item.get("merged_at") is not None,
            "draft": item.get("draft", False),
        }
        for item in response.json()
    ]
    return _gitlab_page(results, response.headers)


def create_project_hook(
    instance_url: str,
    access_token: str,
    *,
    project_path: str,
    hook_url: str,
    secret: str,
) -> GitLabProjectHook:
    encoded_path = quote(project_path, safe="")
    response = requests.post(
        f"{instance_url}/api/v4/projects/{encoded_path}/hooks",
        headers={"PRIVATE-TOKEN": access_token},
        json={
            "url": hook_url,
            "token": secret,
            "issues_events": True,
            "merge_requests_events": True,
            "enable_ssl_verification": True,
        },
        timeout=GITLAB_CLIENT_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    payload = response.json()
    return {"id": payload["id"], "project_id": payload["project_id"]}


def delete_project_hook(
    instance_url: str,
    access_token: str,
    *,
    project_id: int,
    hook_id: int,
) -> None:
    response = requests.delete(
        f"{instance_url}/api/v4/projects/{project_id}/hooks/{hook_id}",
        headers={"PRIVATE-TOKEN": access_token},
        timeout=GITLAB_CLIENT_TIMEOUT_SECONDS,
    )
    if response.status_code == 404:
        return
    response.raise_for_status()


def create_issue_note(
    instance_url: str,
    access_token: str,
    *,
    project_path: str,
    issue_iid: int,
    body: str,
) -> None:
    encoded_path = quote(project_path, safe="")
    response = requests.post(
        f"{instance_url}/api/v4/projects/{encoded_path}/issues/{issue_iid}/notes",
        headers={"PRIVATE-TOKEN": access_token},
        json={"body": body},
        timeout=GITLAB_CLIENT_TIMEOUT_SECONDS,
    )
    response.raise_for_status()


def create_merge_request_note(
    instance_url: str,
    access_token: str,
    *,
    project_path: str,
    merge_request_iid: int,
    body: str,
) -> None:
    encoded_path = quote(project_path, safe="")
    response = requests.post(
        f"{instance_url}/api/v4/projects/{encoded_path}/merge_requests/{merge_request_iid}/notes",
        headers={"PRIVATE-TOKEN": access_token},
        json={"body": body},
        timeout=GITLAB_CLIENT_TIMEOUT_SECONDS,
    )
    response.raise_for_status()


def create_flagsmith_label(
    instance_url: str,
    access_token: str,
    *,
    project_path: str,
) -> bool:
    """Create the "Flagsmith Feature" label on a GitLab project.

    Returns True if the label was created, False if it already existed.
    """
    encoded_path = quote(project_path, safe="")
    try:
        response = requests.post(
            f"{instance_url}/api/v4/projects/{encoded_path}/labels",
            headers={"PRIVATE-TOKEN": access_token},
            json={
                "name": GITLAB_FLAGSMITH_LABEL,
                "color": GITLAB_FLAGSMITH_LABEL_COLOUR,
                "description": GITLAB_FLAGSMITH_LABEL_DESCRIPTION,
            },
            timeout=GITLAB_CLIENT_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 409:
            return False
        raise
    return True


def add_flagsmith_label_to_gitlab_resource(
    instance_url: str,
    access_token: str,
    *,
    project_path: str,
    resource_kind: GitLabResourceKind,
    resource_iid: int,
) -> None:
    """Apply the "Flagsmith Feature" label to a GitLab issue or MR, additively."""
    encoded_path = quote(project_path, safe="")
    response = requests.put(
        f"{instance_url}/api/v4/projects/{encoded_path}/{resource_kind}/{resource_iid}",
        headers={"PRIVATE-TOKEN": access_token},
        json={"add_labels": GITLAB_FLAGSMITH_LABEL},
        timeout=GITLAB_CLIENT_TIMEOUT_SECONDS,
    )
    response.raise_for_status()


def remove_flagsmith_label_from_gitlab_resource(
    instance_url: str,
    access_token: str,
    *,
    project_path: str,
    resource_kind: GitLabResourceKind,
    resource_iid: int,
) -> None:
    """Remove the "Flagsmith Feature" label from a GitLab issue or MR."""
    encoded_path = quote(project_path, safe="")
    response = requests.put(
        f"{instance_url}/api/v4/projects/{encoded_path}/{resource_kind}/{resource_iid}",
        headers={"PRIVATE-TOKEN": access_token},
        json={"remove_labels": GITLAB_FLAGSMITH_LABEL},
        timeout=GITLAB_CLIENT_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
