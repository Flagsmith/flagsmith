import json
import logging
from enum import Enum
from typing import Any

import requests
from django.conf import settings
from github import Auth, Github
from requests.exceptions import HTTPError

from integrations.github.constants import (
    GITHUB_API_CALLS_TIMEOUT,
    GITHUB_API_URL,
    GITHUB_API_VERSION,
    GITHUB_FLAGSMITH_LABEL,
    GITHUB_FLAGSMITH_LABEL_COLOR,
    GITHUB_FLAGSMITH_LABEL_DESCRIPTION,
)
from integrations.github.dataclasses import (
    IssueQueryParams,
    PaginatedQueryParams,
    RepoQueryParams,
)
from integrations.github.models import GithubConfiguration

logger = logging.getLogger(__name__)


class ResourceType(Enum):
    ISSUES = "issue"
    PULL_REQUESTS = "pr"


def build_request_headers(
    installation_id: str, use_jwt: bool = False
) -> dict[str, str]:
    token = (
        generate_jwt_token(settings.GITHUB_APP_ID)
        if use_jwt
        else generate_token(
            installation_id,
            settings.GITHUB_APP_ID,
        )
    )

    return {
        "X-GitHub-Api-Version": GITHUB_API_VERSION,
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {token}",
    }


# TODO: Add test coverage for this function
def generate_token(installation_id: str, app_id: int) -> str:  # pragma: no cover
    auth: Auth.AppInstallationAuth = Auth.AppAuth(
        app_id=int(app_id), private_key=settings.GITHUB_PEM
    ).get_installation_auth(
        installation_id=int(installation_id),
        token_permissions=None,
    )
    Github(auth=auth)
    token = auth.token
    return token


# TODO: Add test coverage for this function
def generate_jwt_token(app_id: int) -> str:  # pragma: no cover
    github_auth: Auth.AppAuth = Auth.AppAuth(
        app_id=app_id,
        private_key=settings.GITHUB_PEM,
    )
    token = github_auth.create_jwt()
    return token


def build_paginated_response(
    results: list[dict[str, Any]],
    response: requests.Response,
    total_count: int | None = None,
    incomplete_results: bool | None = None,
) -> dict[str, Any]:
    data: dict[str, Any] = {
        "results": results,
    }

    if response.links.get("prev"):
        data["previous"] = response.links.get("prev")

    if response.links.get("next"):
        data["next"] = response.links.get("next")

    if total_count:
        data["total_count"] = total_count

    if incomplete_results:
        data["incomplete_results"] = incomplete_results

    return data


def post_comment_to_github(
    installation_id: str, owner: str, repo: str, issue: str, body: str
) -> dict[str, Any]:

    url = f"{GITHUB_API_URL}repos/{owner}/{repo}/issues/{issue}/comments"
    headers = build_request_headers(installation_id)
    payload = {"body": body}
    response = requests.post(
        url, json=payload, headers=headers, timeout=GITHUB_API_CALLS_TIMEOUT
    )
    response.raise_for_status()

    return response.json()


def delete_github_installation(installation_id: str) -> requests.Response:
    url = f"{GITHUB_API_URL}app/installations/{installation_id}"
    headers = build_request_headers(installation_id, use_jwt=True)
    response = requests.delete(url, headers=headers, timeout=GITHUB_API_CALLS_TIMEOUT)
    response.raise_for_status()
    return response


def fetch_search_github_resource(
    resource_type: ResourceType,
    organisation_id: int,
    params: IssueQueryParams,
) -> dict[str, Any]:
    github_configuration = GithubConfiguration.objects.get(
        organisation_id=organisation_id, deleted_at__isnull=True
    )
    # Build Github search query
    q = ["q="]
    if params.search_text:
        q.append(params.search_text)
    q.append(f"repo:{params.repo_owner}/{params.repo_name}")
    q.append(f"is:{resource_type.value}")
    if params.state:
        q.append(f"is:{params.state}")
    q.append("in:title")
    if params.search_in_body:
        q.append("in:body")
    if params.search_in_comments:
        q.append("in:comments")
    if params.author:
        q.append(f"author:{params.author}")
    if params.assignee:
        q.append(f"assignee:{params.assignee}")

    url = (
        f"{GITHUB_API_URL}search/issues?"
        + " ".join(q)
        + f"&per_page={params.page_size}&page={params.page}"
    )
    headers: dict[str, str] = build_request_headers(
        github_configuration.installation_id
    )
    try:
        response = requests.get(url, headers=headers, timeout=GITHUB_API_CALLS_TIMEOUT)
        response.raise_for_status()
        json_response = response.json()

    except HTTPError:
        response_content = response.content.decode("utf-8")
        error_message = (
            "The resources do not exist or you do not have permission to view them"
        )
        error_data = json.loads(response_content)
        if error_data.get("message", "") == "Validation Failed" and any(
            error.get("code", "") == "invalid" for error in error_data.get("errors", [])
        ):
            logger.warning(error_message)
            raise ValueError(error_message)

    results = [
        {
            "html_url": i["html_url"],
            "id": i["id"],
            "title": i["title"],
            "number": i["number"],
            "state": i["state"],
            "merged": i.get("merged", False),
            "draft": i.get("draft", False),
        }
        for i in json_response["items"]
    ]

    return build_paginated_response(
        results=results,
        response=response,
        total_count=json_response["total_count"],
        incomplete_results=json_response["incomplete_results"],
    )


def fetch_github_repositories(
    installation_id: str,
    params: PaginatedQueryParams,
) -> dict[str, Any]:
    url = (
        f"{GITHUB_API_URL}installation/repositories?"
        + f"&per_page={params.page_size}&page={params.page}"
    )

    headers: dict[str, str] = build_request_headers(installation_id)

    response = requests.get(url, headers=headers, timeout=GITHUB_API_CALLS_TIMEOUT)
    json_response = response.json()
    response.raise_for_status()
    results = [
        {
            "full_name": i["full_name"],
            "id": i["id"],
            "name": i["name"],
        }
        for i in json_response["repositories"]
    ]

    return build_paginated_response(results, response, json_response["total_count"])


def get_github_issue_pr_title_and_state(
    organisation_id: int, resource_url: str
) -> dict[str, str]:
    url_parts = resource_url.split("/")
    owner = url_parts[-4]
    repo = url_parts[-3]
    number = url_parts[-1]
    installation_id = GithubConfiguration.objects.get(
        organisation_id=organisation_id, deleted_at__isnull=True
    ).installation_id

    url = f"{GITHUB_API_URL}repos/{owner}/{repo}/issues/{number}"
    headers = build_request_headers(installation_id)
    response = requests.get(url, headers=headers, timeout=GITHUB_API_CALLS_TIMEOUT)
    response.raise_for_status()
    json_response = response.json()
    return {"title": json_response["title"], "state": json_response["state"]}


def fetch_github_repo_contributors(
    organisation_id: int,
    params: RepoQueryParams,
) -> dict[str, Any]:
    installation_id = GithubConfiguration.objects.get(
        organisation_id=organisation_id, deleted_at__isnull=True
    ).installation_id

    url = (
        f"{GITHUB_API_URL}repos/{params.repo_owner}/{params.repo_name}/contributors?"
        + f"&per_page={params.page_size}&page={params.page}"
    )

    headers = build_request_headers(installation_id)
    response = requests.get(url, headers=headers, timeout=GITHUB_API_CALLS_TIMEOUT)
    response.raise_for_status()
    json_response = response.json()

    results = [
        {
            "login": i["login"],
            "avatar_url": i["avatar_url"],
            "contributions": i["contributions"],
        }
        for i in json_response
    ]

    return build_paginated_response(results, response)


def create_flagsmith_flag_label(
    installation_id: str, owner: str, repo: str
) -> dict[str, Any]:
    # Create "Flagsmith Flag" label in linked repo
    url = f"{GITHUB_API_URL}repos/{owner}/{repo}/labels"
    headers = build_request_headers(installation_id)
    payload = {
        "name": GITHUB_FLAGSMITH_LABEL,
        "color": GITHUB_FLAGSMITH_LABEL_COLOR,
        "description": GITHUB_FLAGSMITH_LABEL_DESCRIPTION,
    }
    try:
        response = requests.post(
            url, json=payload, headers=headers, timeout=GITHUB_API_CALLS_TIMEOUT
        )
        response.raise_for_status()
        return response.json()

    except HTTPError:
        response_content = response.content.decode("utf-8")
        error_data = json.loads(response_content)
        if any(
            error["code"] == "already_exists" for error in error_data.get("errors", [])
        ):
            logger.warning("Label already exists")
            return {"message": "Label already exists"}, 200


def label_github_issue_pr(
    installation_id: str, owner: str, repo: str, issue: str
) -> dict[str, Any]:
    # Label linked GitHub Issue or PR with the "Flagsmith Flag" label
    url = f"{GITHUB_API_URL}repos/{owner}/{repo}/issues/{issue}/labels"
    headers = build_request_headers(installation_id)
    payload = [GITHUB_FLAGSMITH_LABEL]
    response = requests.post(
        url, json=payload, headers=headers, timeout=GITHUB_API_CALLS_TIMEOUT
    )
    response.raise_for_status()
    return response.json()
