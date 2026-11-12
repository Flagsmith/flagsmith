import base64
import dataclasses
import json

import requests
import structlog
from django.core.serializers.json import DjangoJSONEncoder

from telemetry.dataclasses import UsageSnapshot

logger = structlog.get_logger(__name__)

USAGE_ENDPOINT_PATH = "/v1/public/usage"
REQUEST_TIMEOUT_SECONDS = 30


def post_usage_snapshot(
    *,
    base_url: str,
    snapshot: UsageSnapshot,
    signature_b64: str,
) -> None:
    url = f"{base_url.rstrip('/')}{USAGE_ENDPOINT_PATH}"
    headers = {
        "Authorization": (f"Bearer {_map_signature_to_bearer_token(signature_b64)}"),
        "Content-Type": "application/json",
    }
    body = json.dumps(dataclasses.asdict(snapshot), cls=DjangoJSONEncoder)

    response = requests.post(
        url,
        data=body,
        headers=headers,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )

    if response.ok:
        logger.info("snapshot.pushed", status_code=response.status_code)
    else:
        logger.warning("snapshot.push_failed", status_code=response.status_code)


def _map_signature_to_bearer_token(signature_b64: str) -> str:
    raw_signature = base64.b64decode(signature_b64)
    return base64.urlsafe_b64encode(raw_signature).decode("ascii").rstrip("=")
