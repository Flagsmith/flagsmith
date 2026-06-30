import dataclasses
import json

import requests
import structlog
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder

from organisations.models import Organisation
from organisations.usage_reporting.dataclasses import UsageSnapshot
from organisations.usage_reporting.mappers import (
    map_organisation_to_usage_snapshot,
    map_signature_to_control_plane_auth_token,
)

logger = structlog.get_logger("usage_reporting")

USAGE_ENDPOINT_PATH = "/v1/public/usage"
REQUEST_TIMEOUT_SECONDS = 30


def get_licensed_organisations() -> list[Organisation]:
    if not settings.LICENSING_INSTALLED:
        return []
    return list(
        Organisation.objects.filter(licence__isnull=False).select_related("licence")
    )


def push_snapshot(
    *,
    base_url: str,
    snapshot: UsageSnapshot,
    signature: str,
) -> None:
    url = f"{base_url.rstrip('/')}{USAGE_ENDPOINT_PATH}"
    headers = {
        "Authorization": (
            f"Bearer {map_signature_to_control_plane_auth_token(signature)}"
        ),
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


def push_usage_snapshots() -> None:
    if not (base_url := settings.CONTROL_PLANE_URL):
        logger.debug("run.skipped", reason="control_plane_url_unset")
        return
    if not (organisations := get_licensed_organisations()):
        logger.debug("run.skipped", reason="no_licensed_organisations")
        return

    for organisation in organisations:
        with structlog.contextvars.bound_contextvars(organisation__id=organisation.id):
            try:
                push_snapshot(
                    base_url=base_url,
                    snapshot=map_organisation_to_usage_snapshot(organisation),
                    signature=organisation.licence.signature,
                )
            except Exception:
                logger.exception("snapshot.errored")
