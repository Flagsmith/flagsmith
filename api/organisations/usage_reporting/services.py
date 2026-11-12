import dataclasses
import json
from datetime import datetime, timedelta

import requests
import structlog
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone
from requests.adapters import HTTPAdapter
from urllib3 import Retry

from organisations.models import Organisation, UsageReportingState
from organisations.usage_reporting.dataclasses import UsageSnapshot
from organisations.usage_reporting.mappers import (
    map_organisation_to_usage_snapshot,
    map_signature_to_control_plane_auth_token,
)

logger = structlog.get_logger("usage_reporting")

USAGE_ENDPOINT_PATH = "/v1/public/usage"
REQUEST_TIMEOUT_SECONDS = 30
RETRY_POLICY = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=(429, 500, 502, 503, 504),
    allowed_methods={"POST"},
    raise_on_status=False,
)


def get_licensed_organisations() -> list[Organisation]:
    if not settings.LICENSING_INSTALLED:
        return []
    return list(
        Organisation.objects.filter(licence__isnull=False).select_related(
            "licence", "usage_reporting_state"
        )
    )


def get_window_start(organisation: Organisation, window_end: datetime) -> datetime:
    try:
        return organisation.usage_reporting_state.reported_until
    except UsageReportingState.DoesNotExist:
        return window_end - timedelta(hours=24)


def push_snapshot(
    *,
    base_url: str,
    snapshot: UsageSnapshot,
    signature_b64: str,
) -> None:
    url = f"{base_url.rstrip('/')}{USAGE_ENDPOINT_PATH}"
    headers = {
        "Authorization": (
            f"Bearer {map_signature_to_control_plane_auth_token(signature_b64)}"
        ),
        "Content-Type": "application/json",
    }
    body = json.dumps(dataclasses.asdict(snapshot), cls=DjangoJSONEncoder)

    with requests.Session() as session:
        session.mount("https://", HTTPAdapter(max_retries=RETRY_POLICY))
        response = session.post(
            url=url, data=body, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS
        )

        response.raise_for_status()
        logger.info("snapshot.pushed", status_code=response.status_code)


def push_usage_snapshots() -> None:
    if not (base_url := settings.CONTROL_PLANE_URL):
        logger.debug("run.skipped", reason="control_plane_url_unset")
        return
    if not (organisations := get_licensed_organisations()):
        logger.debug("run.skipped", reason="no_licensed_organisations")
        return

    window_end = timezone.now().replace(minute=0, second=0, microsecond=0)

    for organisation in organisations:
        with structlog.contextvars.bound_contextvars(organisation__id=organisation.id):
            try:
                window_start = get_window_start(organisation, window_end)
                if window_start >= window_end:
                    # The control plane drops snapshots with a repeated timestamp,
                    # so an empty push would make the next window collide and be lost.
                    logger.debug("snapshot.skipped", reason="empty_window")
                    continue

                push_snapshot(
                    base_url=base_url,
                    snapshot=map_organisation_to_usage_snapshot(
                        organisation=organisation,
                        window_start=window_start,
                        window_end=window_end,
                    ),
                    signature_b64=organisation.licence.signature,
                )

                UsageReportingState.objects.update_or_create(
                    organisation=organisation, defaults={"reported_until": window_end}
                )
            except Exception as e:
                logger.exception("snapshot.errored", reason=e)
