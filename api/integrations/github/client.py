from django.conf import settings
from github import Auth, Github


def generate_token(installation_id, app_id: int) -> str:
    auth = Auth.AppAuth(int(app_id), settings.GITHUB_PEM).get_installation_auth(
        int(installation_id),
        None,
    )
    Github(auth=auth)
    token = auth.token
    return token
