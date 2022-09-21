from typing import List

import requests
from django.conf import settings


def send_environment_update_messages(environment_keys: List[str]):
    if not settings.SSE_SERVER_BASE_URL:
        return
    header = {"Authorization": f"Token {settings.SSE_SERVER_TOKEN}"}

    for environment_key in environment_keys:
        url = f"https://{settings.SSE_SERVER_BASE_URL}/sse/environments/{environment_key}/queue-change"
        response = requests.post(url, headers=header)
        response.raise_for_status()


def send_identity_update_message(environment_key: str, identifier: str):
    if not settings.SSE_SERVER_BASE_URL:
        return
    url = f"https://{settings.SSE_SERVER_BASE_URL}/sse/environments/{environment_key}/identities/queue-change"

    payload = {"identifier": identifier}
    header = {"Authorization": f"Token {settings.SSE_SERVER_TOKEN}"}
    response = requests.post(url, headers=header, payload=payload)
    response.raise_for_status()
