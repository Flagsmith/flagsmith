from collections.abc import Mapping
from typing import Any

import requests

from integrations.gitlab.client.types import (
    GitLabIssue,
    GitLabMergeRequest,
    GitLabPage,
    GitLabProject,
    T,
)


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
