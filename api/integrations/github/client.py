import logging
import typing
from enum import Enum

import requests
from django.conf import settings
from github import Auth, Github
from rest_framework import status
from rest_framework.response import Response

from integrations.github.constants import (
    GITHUB_API_CALLS_TIMEOUT,
    GITHUB_API_URL,
    GITHUB_API_VERSION,
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
        generate_token(
            installation_id,
            settings.GITHUB_APP_ID,
        )
        if not use_jwt
        else generate_jwt_token(settings.GITHUB_APP_ID)
    )

    return {
        "X-GitHub-Api-Version": GITHUB_API_VERSION,
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {token}",
    }


# TODO: Add coverage tests for this function
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


# TODO: Add coverage tests for this function
def generate_jwt_token(app_id: int) -> str:  # pragma: no cover
    github_auth: Auth.AppAuth = Auth.AppAuth(
        app_id=app_id,
        private_key=settings.GITHUB_PEM,
    )
    token = github_auth.create_jwt()
    return token


def post_comment_to_github(
    installation_id: str, owner: str, repo: str, issue: str, body: str
) -> typing.Dict[str, typing.Any]:
    token = generate_token(
        installation_id,
        settings.GITHUB_APP_ID,
    )

    url = f"{GITHUB_API_URL}repos/{owner}/{repo}/issues/{issue}/comments"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {token}",
    }

    payload = {"body": body}
    response = response = requests.post(
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


def fetch_github_resource(
    resource_type: ResourceType,
    organisation_id: int,
    repo_owner: str,
    repo_name: str,
    page_size: int = 100,
    page: int = 1,
    search_text: str = "",
) -> Response:
    github_configuration = GithubConfiguration.objects.get(
        organisation_id=organisation_id, deleted_at__isnull=True
    )
    url = f"{GITHUB_API_URL}search/issues?q={search_text} repo:{repo_owner}/{repo_name} is:{resource_type.value} is:open in:title in:body &per_page={page_size}&page={page}"  # noqa E501
    headers: dict[str, str] = build_request_headers(
        github_configuration.installation_id
    )
    response = requests.get(url, headers=headers, timeout=GITHUB_API_CALLS_TIMEOUT)
    response.raise_for_status()
    json_response = response.json()
    results = [
        {
            "html_url": i["html_url"],
            "id": i["id"],
            "title": i["title"],
            "number": i["number"],
        }
        for i in json_response["items"]
    ]
    data = {
        "results": results,
        "count": json_response["total_count"],
        "incomplete_results": json_response["incomplete_results"],
    }
    if response.links.get("prev"):
        data["previous"] = response.links.get("prev")

    if response.links.get("next"):
        data["next"] = response.links.get("next")

    # Return a Response object
    return Response(
        data=data,
        content_type="application/json",
        status=status.HTTP_200_OK,
    )


def fetch_github_repositories(installation_id: str) -> Response:
    url = f"{GITHUB_API_URL}installation/repositories"

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
    data = {
        "repositories": results,
        "total_count": json_response["total_count"],
    }
    return Response(
        data=data,
        content_type="application/json",
        status=status.HTTP_200_OK,
    )


def get_github_issue_pr_name_and_status(
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
    return {"title": response.json()["title"], "state": response.json()["state"]}
