import logging

import requests

from integrations.gitlab.constants import (
    GITLAB_API_CALLS_TIMEOUT,
    GITLAB_FLAGSMITH_LABEL,
    GITLAB_FLAGSMITH_LABEL_COLOUR,
    GITLAB_FLAGSMITH_LABEL_DESCRIPTION,
)
from integrations.gitlab.dataclasses import (
    IssueQueryParams,
    PaginatedQueryParams,
    ProjectQueryParams,
)
from integrations.gitlab.types import (
    GitLabLabel,
    GitLabMember,
    GitLabNote,
    GitLabProject,
    GitLabResource,
    GitLabResourceEndpoint,
    GitLabResourceMetadata,
    PaginatedResponse,
)

logger = logging.getLogger(__name__)


def _build_request_headers(access_token: str) -> dict[str, str]:
    return {"PRIVATE-TOKEN": access_token}


def _build_paginated_response(
    results: list[GitLabProject] | list[GitLabResource] | list[GitLabMember],
    response: requests.Response,
    total_count: int | None = None,
) -> PaginatedResponse:
    data: PaginatedResponse = {"results": results}

    current_page = int(response.headers.get("x-page", 1))
    total_pages = int(response.headers.get("x-total-pages", 1))

    if current_page > 1:
        data["previous"] = current_page - 1
    if current_page < total_pages:
        data["next"] = current_page + 1

    if total_count is not None:
        data["total_count"] = total_count

    return data


def fetch_gitlab_projects(
    instance_url: str,
    access_token: str,
    params: PaginatedQueryParams,
) -> PaginatedResponse:
    url = f"{instance_url}/api/v4/projects"
    response = requests.get(
        url,
        headers=_build_request_headers(access_token),
        params={
            "membership": "true",
            "per_page": str(params.page_size),
            "page": str(params.page),
        },
        timeout=GITLAB_API_CALLS_TIMEOUT,
    )
    response.raise_for_status()

    results: list[GitLabProject] = [
        {
            "id": project["id"],
            "name": project["name"],
            "path_with_namespace": project["path_with_namespace"],
        }
        for project in response.json()
    ]

    total_count = int(response.headers.get("x-total", len(results)))
    return _build_paginated_response(results, response, total_count)


def fetch_search_gitlab_resource(
    resource_type: GitLabResourceEndpoint,
    instance_url: str,
    access_token: str,
    params: IssueQueryParams,
) -> PaginatedResponse:
    """Search issues or merge requests in a GitLab project."""
    url = f"{instance_url}/api/v4/projects/{params.gitlab_project_id}/{resource_type}"
    query_params: dict[str, str | int] = {
        "per_page": params.page_size,
        "page": params.page,
    }
    if params.search_text:
        query_params["search"] = params.search_text
    if params.state:
        query_params["state"] = params.state
    if params.author:
        query_params["author_username"] = params.author
    if params.assignee:
        query_params["assignee_username"] = params.assignee

    response = requests.get(
        url,
        headers=_build_request_headers(access_token),
        params=query_params,
        timeout=GITLAB_API_CALLS_TIMEOUT,
    )
    response.raise_for_status()

    is_mr = resource_type == "merge_requests"
    results: list[GitLabResource] = [
        {
            "web_url": item["web_url"],
            "id": item["id"],
            "title": item["title"],
            "iid": item["iid"],
            "state": item["state"],
            "merged": item.get("merged_at") is not None if is_mr else False,
            "draft": item.get("draft", False) if is_mr else False,
        }
        for item in response.json()
    ]

    total_count = int(response.headers.get("x-total", len(results)))
    return _build_paginated_response(results, response, total_count)


def fetch_gitlab_project_members(
    instance_url: str,
    access_token: str,
    params: ProjectQueryParams,
) -> PaginatedResponse:
    url = f"{instance_url}/api/v4/projects/{params.gitlab_project_id}/members"
    response = requests.get(
        url,
        headers=_build_request_headers(access_token),
        params={"per_page": params.page_size, "page": params.page},
        timeout=GITLAB_API_CALLS_TIMEOUT,
    )
    response.raise_for_status()

    results: list[GitLabMember] = [
        {
            "username": member["username"],
            "avatar_url": member["avatar_url"],
            "name": member["name"],
        }
        for member in response.json()
    ]

    return _build_paginated_response(results, response)


def create_gitlab_issue(
    instance_url: str,
    access_token: str,
    gitlab_project_id: int,
    title: str,
    body: str,
) -> dict[str, object]:
    url = f"{instance_url}/api/v4/projects/{gitlab_project_id}/issues"
    response = requests.post(
        url,
        json={"title": title, "description": body},
        headers=_build_request_headers(access_token),
        timeout=GITLAB_API_CALLS_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()  # type: ignore[no-any-return]


def post_comment_to_gitlab(
    instance_url: str,
    access_token: str,
    gitlab_project_id: int,
    resource_type: GitLabResourceEndpoint,
    resource_iid: int,
    body: str,
) -> GitLabNote:
    """Post a note (comment) on a GitLab issue or merge request."""
    url = (
        f"{instance_url}/api/v4/projects/{gitlab_project_id}"
        f"/{resource_type}/{resource_iid}/notes"
    )
    response = requests.post(
        url,
        json={"body": body},
        headers=_build_request_headers(access_token),
        timeout=GITLAB_API_CALLS_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()  # type: ignore[no-any-return]


def get_gitlab_resource_metadata(
    instance_url: str,
    access_token: str,
    gitlab_project_id: int,
    resource_type: GitLabResourceEndpoint,
    resource_iid: int,
) -> GitLabResourceMetadata:
    """Fetch title and state for a GitLab issue or MR."""
    url = (
        f"{instance_url}/api/v4/projects/{gitlab_project_id}"
        f"/{resource_type}/{resource_iid}"
    )
    response = requests.get(
        url,
        headers=_build_request_headers(access_token),
        timeout=GITLAB_API_CALLS_TIMEOUT,
    )
    response.raise_for_status()
    json_response = response.json()
    return {"title": json_response["title"], "state": json_response["state"]}


def create_flagsmith_flag_label(
    instance_url: str,
    access_token: str,
    gitlab_project_id: int,
) -> GitLabLabel | None:
    """Create the Flagsmith Flag label on a GitLab project.

    Returns None if the label already exists.
    """
    url = f"{instance_url}/api/v4/projects/{gitlab_project_id}/labels"
    response = requests.post(
        url,
        json={
            "name": GITLAB_FLAGSMITH_LABEL,
            "color": f"#{GITLAB_FLAGSMITH_LABEL_COLOUR}",
            "description": GITLAB_FLAGSMITH_LABEL_DESCRIPTION,
        },
        headers=_build_request_headers(access_token),
        timeout=GITLAB_API_CALLS_TIMEOUT,
    )
    if response.status_code == 409:
        logger.info(
            "Flagsmith Flag label already exists on project %s", gitlab_project_id
        )
        return None

    response.raise_for_status()
    return response.json()  # type: ignore[no-any-return]


def label_gitlab_resource(
    instance_url: str,
    access_token: str,
    gitlab_project_id: int,
    resource_type: GitLabResourceEndpoint,
    resource_iid: int,
) -> dict[str, object]:
    """Add the Flagsmith Flag label to a GitLab issue or MR."""
    url = (
        f"{instance_url}/api/v4/projects/{gitlab_project_id}"
        f"/{resource_type}/{resource_iid}"
    )
    response = requests.put(
        url,
        json={"add_labels": GITLAB_FLAGSMITH_LABEL},
        headers=_build_request_headers(access_token),
        timeout=GITLAB_API_CALLS_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()  # type: ignore[no-any-return]
