import json

import requests
from core.constants import FLAGSMITH_SIGNATURE_HEADER
from core.signing import sign_payload
from django.conf import settings

from environments.dynamodb.migrator import IdentityMigrator
from task_processor.decorators import register_task_handler
from task_processor.models import TaskPriority


def _should_forward(project_id: int) -> bool:
    migrator = IdentityMigrator(project_id)
    return bool(migrator.is_migration_done)


@register_task_handler(queue_size=2000, priority=TaskPriority.LOW)
def forward_identity_request(
    request_method: str,
    headers: dict,
    project_id: int,
    query_params: dict = None,
    request_data: dict = None,
):
    if not _should_forward(project_id):
        return

    url = settings.EDGE_API_URL + "identities/"
    headers = _get_headers(
        request_method, headers, json.dumps(request_data) if request_data else ""
    )
    if request_method == "POST":
        requests.post(url, data=json.dumps(request_data), headers=headers, timeout=5)
        return
    requests.get(url, params=query_params, headers=headers, timeout=5)


@register_task_handler(queue_size=2000, priority=TaskPriority.LOW)
def forward_trait_request(
    request_method: str,
    headers: dict,
    project_id: int,
    payload: dict,
):
    return forward_trait_request_sync(request_method, headers, project_id, payload)


def forward_trait_request_sync(
    request_method: str, headers: dict, project_id: int, payload: dict
):
    if not _should_forward(project_id):
        return

    url = settings.EDGE_API_URL + "traits/"
    payload = json.dumps(payload)
    requests.post(
        url,
        data=payload,
        headers=_get_headers(request_method, headers, payload),
        timeout=5,
    )


@register_task_handler(queue_size=1000, priority=TaskPriority.LOW)
def forward_trait_requests(
    request_method: str,
    headers: str,
    project_id: int,
    payload: dict,
):
    for trait_data in payload:
        forward_trait_request_sync(request_method, headers, project_id, trait_data)


def _get_headers(request_method: str, headers: dict, payload: str = "") -> dict:
    headers = {k: v for k, v in headers.items()}
    # Django by default sets the content-length to "", which in the case of get request(lack of content body)
    # Remains an empty string - an invalid value(according to edge alb and HTTP spec).
    # Hence, we need to remove this header to turn this into a valid request
    # ref: https://groups.google.com/g/django-developers/c/xjYVJN-RguA/m/G9krDqawchQJ
    if request_method == "GET":
        headers.pop("Content-Length", None)
    signature = sign_payload(payload, settings.EDGE_REQUEST_SIGNING_KEY)
    headers[FLAGSMITH_SIGNATURE_HEADER] = signature
    return headers
