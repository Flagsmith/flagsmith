import logging
import typing
from enum import Enum

import requests
from django.conf import settings
from github import Auth, Github

from integrations.github.constants import GITHUB_API_URL, GITHUB_API_VERSION
from integrations.github.models import GithubConfiguration
from organisations.models import Organisation

logger = logging.getLogger(__name__)


class ResourceType(Enum):
    ISSUES = "issues"
    PULL_REQUESTS = "pulls"


def build_request_headers(installation_id: str, useJWT: bool = False) -> dict[str, str]:
    token = (
        generate_token(
            installation_id,
            settings.GITHUB_APP_ID,
        )
        if not useJWT
        else generate_jwt_token(settings.GITHUB_APP_ID)
    )

    return {
        "X-GitHub-Api-Version": GITHUB_API_VERSION,
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {token}",
    }


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
    response = response = requests.post(url, json=payload, headers=headers, timeout=10)
    response.raise_for_status()

    return response.json()


def delete_github_installation(installation_id: str) -> requests.Response:
    url = f"{GITHUB_API_URL}app/installations/{installation_id}"
    headers = build_request_headers(installation_id, useJWT=True)
    response = requests.delete(url, headers=headers, timeout=10)
    return response


def fetch_github_resource(
    resource_type: ResourceType, organisation_id: int, repo_owner: str, repo_name: str
) -> requests.Response:
    organisation = Organisation.objects.get(id=organisation_id)
    github_configuration = GithubConfiguration.objects.get(
        organisation=organisation, deleted_at__isnull=True
    )
    url = f"{GITHUB_API_URL}repos/{repo_owner}/{repo_name}/{resource_type.value}"
    headers: dict[str, str] = build_request_headers(
        github_configuration.installation_id
    )
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return response


def fetch_github_repositories(installation_id: str) -> requests.Response:
    url = f"{GITHUB_API_URL}installation/repositories"

    headers: dict[str, str] = build_request_headers(installation_id)

    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return response
