import datetime

import jwt
import requests
from django.conf import settings
from github import Auth, Github

from integrations.github.constants import (
    GITHUB_API_URL,
    GITHUB_API_VERSION,
    INVALID_INSTALLATION_ID,
)
from integrations.github.models import GithubConfiguration


def check_if_installation_id_is_valid(
    github_configuration: GithubConfiguration,
) -> bool:
    private_key = settings.GITHUB_PEM
    now = datetime.datetime.now(datetime.UTC)

    expiration_time = now + datetime.timedelta(minutes=2)
    payload = {
        "iat": int(now.timestamp()),
        "exp": int(expiration_time.timestamp()),
        "iss": settings.GITHUB_APP_ID,
    }

    token = jwt.encode(payload, private_key, algorithm="RS256")
    url = f"{GITHUB_API_URL}app/installations/{github_configuration.installation_id}"
    headers = {
        "X-GitHub-Api-Version": GITHUB_API_VERSION,
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"Bearer {token}",
    }
    response = requests.get(url, headers=headers, timeout=10)
    if response.status_code == 404:
        github_configuration.update_status(INVALID_INSTALLATION_ID)
        return False
    else:
        return True


def generate_token(installation_id: str, app_id: int) -> str:
    auth: Auth.AppInstallationAuth = Auth.AppAuth(
        app_id=int(app_id), private_key=settings.GITHUB_PEM
    ).get_installation_auth(
        installation_id=int(installation_id),
        token_permissions=None,
    )
    Github(auth=auth)
    token = auth.token
    return token
