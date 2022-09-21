import requests
from django.conf import settings


def send_environment_update_msg(environment_key: str):
    if not settings.SSE_SERVER_BASE_URL:
        return
    url = f"https://{settings.SSE_SERVER_BASE_URL}/sse/environments/{environment_key}/queue-change"
    header = {"Authorization": f"Token {settings.SSE_SERVER_TOKEN}"}
    response = requests.post(url, headers=header)
    response.raise_for_status()


def send_identity_update_msg(environment_key: str, identifier: str):
    if not settings.SSE_SERVER_BASE_URL:
        return
    url = f"https://{settings.SSE_SERVER_BASE_URL}/sse/environments/{environment_key}/identities/queue-change"

    payload = {"identifier": identifier}
    header = {"Authorization": f"Token {settings.SSE_SERVER_TOKEN}"}
    response = requests.post(url, headers=header, payload=payload)
    response.raise_for_status()
