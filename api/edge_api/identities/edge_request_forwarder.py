import json
from typing import Any

import requests
from django.conf import settings

from core.constants import FLAGSMITH_SIGNATURE_HEADER
from core.signing import sign_payload
from environments.dynamodb.migrator import IdentityMigrator


def forward_identity_request(  # type: ignore[no-untyped-def]
    request_method: str,
    headers: dict,  # type: ignore[type-arg]
    project_id: int,
    query_params: dict = None,  # type: ignore[type-arg,assignment]
    request_data: dict = None,  # type: ignore[type-arg,assignment]
):
    if not _should_forward(project_id):
        return

    url = settings.EDGE_API_URL + "identities/"  # type: ignore[operator]
    headers = _get_headers(
        request_method, headers, json.dumps(request_data) if request_data else ""
    )
    if request_method == "POST":
        requests.post(url, data=json.dumps(request_data), headers=headers, timeout=5)
        return
    requests.get(url, params=query_params, headers=headers, timeout=5)


def forward_trait_request(  # type: ignore[no-untyped-def]
    request_method: str,
    headers: dict[str, str],
    project_id: int,
    payload: dict[str, Any],
):
    if not _should_forward(project_id):
        return

    url = settings.EDGE_API_URL + "traits/"  # type: ignore[operator]
    payload = json.dumps(payload)  # type: ignore[assignment]
    requests.post(
        url,
        data=payload,
        headers=_get_headers(request_method, headers, payload),  # type: ignore[arg-type]
        timeout=5,
    )


def forward_trait_requests(  # type: ignore[no-untyped-def]
    request_method: str,
    headers: dict[str, str],
    project_id: int,
    payload: list[dict[str, Any]],
):
    for trait_data in payload:
        forward_trait_request(request_method, headers, project_id, trait_data)


def _should_forward(project_id: int) -> bool:
    migrator = IdentityMigrator(project_id)  # type: ignore[no-untyped-call]
    return bool(migrator.is_migration_done)


def _get_headers(request_method: str, headers: dict, payload: str = "") -> dict:  # type: ignore[type-arg]
    headers = {k: v for k, v in headers.items()}
    # Django by default sets the content-length to "", which in the case of get request(lack of content body)
    # Remains an empty string - an invalid value(according to edge alb and HTTP spec).
    # Hence, we need to remove this header to turn this into a valid request
    # ref: https://groups.google.com/g/django-developers/c/xjYVJN-RguA/m/G9krDqawchQJ
    if request_method == "GET":
        headers.pop("Content-Length", None)
    signature = sign_payload(payload, settings.EDGE_REQUEST_SIGNING_KEY)  # type: ignore[arg-type]
    headers[FLAGSMITH_SIGNATURE_HEADER] = signature
    return headers
