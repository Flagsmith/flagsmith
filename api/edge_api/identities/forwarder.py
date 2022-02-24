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
    if request.method == "POST":
        _forward_identity_post_request(request, url)
        return
    _forward_identity_get_request(request, url)


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


def _get_headers(request: Request, payload: str = "") -> dict:
    headers = {k: v for k, v in request.headers.items()}
    signature = sign_payload(payload, settings.EDGE_REQUEST_SIGNING_KEY)
    headers[FLAGSMITH_SIGNATURE_HEADER] = signature
    return headers
