from typing import List

import requests
from django.conf import settings

from task_processor.decorators import register_task_handler

from .exceptions import SSEAuthTokenNotSet


@register_task_handler()
def send_environment_update_messages(environment_keys: List[str]):
    for environment_key in environment_keys:
        send_environment_update_message(environment_key)


@register_task_handler()
def send_environment_update_message(environment_key: str):
    url = f"{settings.SSE_SERVER_BASE_URL}/sse/environments/{environment_key}/queue-change"
    response = requests.post(url, headers=get_auth_header())
    response.raise_for_status()


@register_task_handler()
def send_identity_update_message(environment_key: str, identifier: str):
    url = f"{settings.SSE_SERVER_BASE_URL}/sse/environments/{environment_key}/identities/queue-change"
    payload = {"identifier": identifier}

    response = requests.post(url, headers=get_auth_header(), json=payload)
    response.raise_for_status()


@register_task_handler()
def send_identity_update_messages(environment_key: str, identifiers: List[str]):
    for identifier in identifiers:
        send_identity_update_message(environment_key, identifier)


def get_auth_header():
    if not settings.SSE_AUTHENTICATION_TOKEN:
        raise SSEAuthTokenNotSet()

    return {"Authorization": f"Token {settings.SSE_AUTHENTICATION_TOKEN}"}
