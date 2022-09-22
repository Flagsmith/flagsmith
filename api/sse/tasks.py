from typing import List

import requests
from django.conf import settings

from task_processor.decorators import register_task_handler


@register_task_handler()
def send_environment_update_messages(environment_keys: List[str]):
    if not settings.SSE_SERVER_BASE_URL:
        return

    for environment_key in environment_keys:
        url = f"{settings.SSE_SERVER_BASE_URL}/sse/environments/{environment_key}/queue-change"
        response = requests.post(url, headers=get_auth_header())
        response.raise_for_status()


@register_task_handler()
def send_identity_update_message(environment_key: str, identifier: str):
    if not settings.SSE_SERVER_BASE_URL:
        return
    url = f"{settings.SSE_SERVER_BASE_URL}/sse/environments/{environment_key}/identities/queue-change"

    payload = {"identifier": identifier}
    response = requests.post(url, headers=get_auth_header(), json=payload)
    response.raise_for_status()


def get_auth_header():
    return {"Authorization": f"Token {settings.SSE_AUTHENTICATION_TOKEN}"}
