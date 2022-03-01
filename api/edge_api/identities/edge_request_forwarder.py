import json

import requests
from core.constants import FLAGSMITH_SIGNATURE_HEADER
from core.signing import sign_payload
from django.conf import settings
from rest_framework.request import Request

from environments.dynamodb import DynamoIdentityWrapper
from util.util import postpone


def _should_forward(project_id: int) -> bool:
    dynamo_identity_wrapper = DynamoIdentityWrapper()
    return dynamo_identity_wrapper.is_migration_done(project_id)


@postpone
def forward_identity_request(request, project_id: int):
    forward_identity_request_sync(request, project_id)


def forward_identity_request_sync(request, project_id: int):
    if not _should_forward(project_id):
        return

    url = settings.EDGE_API_URL + "identities/"
    forwarding_method = (
        _forward_identity_post_request
        if request.method == "POST"
        else _forward_identity_get_request
    )
    forwarding_method(request, url)


def _forward_identity_get_request(request: Request, url: str):
    requests.get(
        url,
        params=request.GET.dict(),
        headers=_get_headers(request),
    )


def _forward_identity_post_request(request: Request, url: str):
    payload = json.dumps(request.data)
    requests.post(
        url,
        data=payload,
        headers=_get_headers(request, payload),
    )


@postpone
def forward_trait_request(request: Request, project_id: int, payload: dict = None):
    return forward_trait_request_sync(request, project_id, payload)


def forward_trait_request_sync(request: Request, project_id: int, payload: dict = None):
    if not _should_forward(project_id):
        return

    url = settings.EDGE_API_URL + "traits/"
    payload = payload if payload else request.data
    payload = json.dumps(payload)
    requests.post(
        url,
        data=payload,
        headers=_get_headers(request, payload),
    )


@postpone
def forward_trait_requests(request: Request, project_id: int):
    for trait_data in request.data:
        return forward_trait_request_sync(request, project_id, payload=trait_data)


def _get_headers(request: Request, payload: str = "") -> dict:
    headers = {k: v for k, v in request.headers.items()}
    # Django by default sets the content-length to "", which in the case of get request(lack of content body)
    # Remains an empty string - an invalid value(according to edge alb and HTTP spec).
    # Hence, we need to remove this header to turn this into a valid request
    # ref: https://groups.google.com/g/django-developers/c/xjYVJN-RguA/m/G9krDqawchQJ
    if request.method == "GET":
        headers.pop("Content-Length", None)
    signature = sign_payload(payload, settings.EDGE_REQUEST_SIGNING_KEY)
    headers[FLAGSMITH_SIGNATURE_HEADER] = signature
    return headers
