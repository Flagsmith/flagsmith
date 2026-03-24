import json
import logging
from typing import Any

import requests
from requests.exceptions import HTTPError

from integrations.gitlab.constants import (
    GITLAB_API_CALLS_TIMEOUT,
    GITLAB_FLAGSMITH_LABEL,
    GITLAB_FLAGSMITH_LABEL_COLOR,
    GITLAB_FLAGSMITH_LABEL_DESCRIPTION,
)
from integrations.gitlab.dataclasses import (
    IssueQueryParams,
    PaginatedQueryParams,
    ProjectQueryParams,
)

logger = logging.getLogger(__name__)


def build_request_headers(access_token: str) -> dict[str, str]:
    return {"PRIVATE-TOKEN": access_token}


def build_paginated_response(
    results: list[dict[str, Any]],
    response: requests.Response,
    total_count: int | None = None,
) -> dict[str, Any]:
    data: dict[str, Any] = {"results": results}

    # GitLab uses X-Page and X-Total-Pages headers for pagination
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
) -> dict[str, Any]:
    url = (
        f"{instance_url}/api/v4/projects"
        f"?membership=true&per_page={params.page_size}&page={params.page}"
    )
    headers = build_request_headers(access_token)
    response = requests.get(url, headers=headers, timeout=GITLAB_API_CALLS_TIMEOUT)
    response.raise_for_status()
    json_response = response.json()

    results = [
        {
            "id": project["id"],
            "name": project["name"],
            "path_with_namespace": project["path_with_namespace"],
        }
        for project in json_response
    ]

    total_count = int(response.headers.get("x-total", len(results)))
    return build_paginated_response(results, response, total_count)


def fetch_search_gitlab_resource(
    resource_type: str,
    instance_url: str,
    access_token: str,
    params: IssueQueryParams,
) -> dict[str, Any]:
    """Search issues or merge requests in a GitLab project.

    resource_type: "issue" or "merge_request"
    """
    endpoint = "issues" if resource_type == "issue" else "merge_requests"
    url = (
        f"{instance_url}/api/v4/projects/{params.gitlab_project_id}/{endpoint}"
        f"?per_page={params.page_size}&page={params.page}"
    )
    if params.search_text:
        url += f"&search={params.search_text}"
    if params.state:
        url += f"&state={params.state}"
    if params.author:
        url += f"&author_username={params.author}"
    if params.assignee:
        url += f"&assignee_username={params.assignee}"

    headers = build_request_headers(access_token)
    response = requests.get(url, headers=headers, timeout=GITLAB_API_CALLS_TIMEOUT)
    response.raise_for_status()
    json_response = response.json()

    results = [
        {
            "web_url": item["web_url"],
            "id": item["id"],
            "title": item["title"],
            "iid": item["iid"],
            "state": item["state"],
            "merged": item.get("merged_at") is not None
            if resource_type == "merge_request"
            else False,
            "draft": item.get("draft", False)
            if resource_type == "merge_request"
            else False,
        }
        for item in json_response
    ]

    total_count = int(response.headers.get("x-total", len(results)))
    return build_paginated_response(results, response, total_count)


def fetch_gitlab_project_members(
    instance_url: str,
    access_token: str,
    params: ProjectQueryParams,
) -> dict[str, Any]:
    url = (
        f"{instance_url}/api/v4/projects/{params.gitlab_project_id}/members"
        f"?per_page={params.page_size}&page={params.page}"
    )
    headers = build_request_headers(access_token)
    response = requests.get(url, headers=headers, timeout=GITLAB_API_CALLS_TIMEOUT)
    response.raise_for_status()
    json_response = response.json()

    results = [
        {
            "username": member["username"],
            "avatar_url": member["avatar_url"],
            "name": member["name"],
        }
        for member in json_response
    ]

    return build_paginated_response(results, response)


def create_gitlab_issue(
    instance_url: str,
    access_token: str,
    gitlab_project_id: int,
    title: str,
    body: str,
) -> dict[str, Any]:
    url = f"{instance_url}/api/v4/projects/{gitlab_project_id}/issues"
    headers = build_request_headers(access_token)
    payload = {"title": title, "description": body}
    response = requests.post(
        url, json=payload, headers=headers, timeout=GITLAB_API_CALLS_TIMEOUT
    )
    response.raise_for_status()
    return response.json()  # type: ignore[no-any-return]


def post_comment_to_gitlab(
    instance_url: str,
    access_token: str,
    gitlab_project_id: int,
    resource_type: str,
    resource_iid: int,
    body: str,
) -> dict[str, Any]:
    """Post a note (comment) on a GitLab issue or merge request.

    resource_type: "issues" or "merge_requests"
    """
    url = (
        f"{instance_url}/api/v4/projects/{gitlab_project_id}"
        f"/{resource_type}/{resource_iid}/notes"
    )
    headers = build_request_headers(access_token)
    payload = {"body": body}
    response = requests.post(
        url, json=payload, headers=headers, timeout=GITLAB_API_CALLS_TIMEOUT
    )
    response.raise_for_status()
    return response.json()  # type: ignore[no-any-return]


def get_gitlab_issue_mr_title_and_state(
    instance_url: str,
    access_token: str,
    gitlab_project_id: int,
    resource_type: str,
    resource_iid: int,
) -> dict[str, str]:
    """Fetch title and state for a GitLab issue or MR.

    resource_type: "issues" or "merge_requests"
    """
    url = (
        f"{instance_url}/api/v4/projects/{gitlab_project_id}"
        f"/{resource_type}/{resource_iid}"
    )
    headers = build_request_headers(access_token)
    response = requests.get(url, headers=headers, timeout=GITLAB_API_CALLS_TIMEOUT)
    response.raise_for_status()
    json_response = response.json()
    return {"title": json_response["title"], "state": json_response["state"]}


def create_flagsmith_flag_label(
    instance_url: str,
    access_token: str,
    gitlab_project_id: int,
) -> dict[str, Any] | None:
    url = f"{instance_url}/api/v4/projects/{gitlab_project_id}/labels"
    headers = build_request_headers(access_token)
    payload = {
        "name": GITLAB_FLAGSMITH_LABEL,
        "color": f"#{GITLAB_FLAGSMITH_LABEL_COLOR}",
        "description": GITLAB_FLAGSMITH_LABEL_DESCRIPTION,
    }
    try:
        response = requests.post(
            url, json=payload, headers=headers, timeout=GITLAB_API_CALLS_TIMEOUT
        )
        response.raise_for_status()
        return response.json()  # type: ignore[no-any-return]
    except HTTPError:
        response_content = response.content.decode("utf-8")
        error_data = json.loads(response_content)
        if "already exists" in str(error_data.get("message", "")):
            logger.warning("Label already exists")
            return None
        raise


def label_gitlab_issue_mr(
    instance_url: str,
    access_token: str,
    gitlab_project_id: int,
    resource_type: str,
    resource_iid: int,
) -> dict[str, Any]:
    """Add the Flagsmith Flag label to a GitLab issue or MR.

    resource_type: "issues" or "merge_requests"
    """
    url = (
        f"{instance_url}/api/v4/projects/{gitlab_project_id}"
        f"/{resource_type}/{resource_iid}"
    )
    headers = build_request_headers(access_token)
    payload = {"add_labels": GITLAB_FLAGSMITH_LABEL}
    response = requests.put(
        url, json=payload, headers=headers, timeout=GITLAB_API_CALLS_TIMEOUT
    )
    response.raise_for_status()
    return response.json()  # type: ignore[no-any-return]
