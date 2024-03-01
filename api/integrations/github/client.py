from github import Auth, Github

from integrations.github.constants import GITHUB_PEM


def generate_token(installation_id, app_id):
    auth = Auth.AppAuth(int(app_id), GITHUB_PEM).get_installation_auth(
        int(installation_id),
        None,
    )
    Github(auth=auth)
    token = auth.token
    return token
