import json
import logging
from typing import Any

import requests

from audit.models import AuditLog
from integrations.common.wrapper import AbstractBaseEventIntegrationWrapper
from integrations.grafana.mappers import (
    map_audit_log_record_to_grafana_annotation,
)

logger = logging.getLogger(__name__)

ROUTE_API_ANNOTATIONS = "/api/annotations"


class GrafanaWrapper(AbstractBaseEventIntegrationWrapper):
    def __init__(self, base_url: str, api_key: str) -> None:
        base_url = base_url[:-1] if base_url.endswith("/") else base_url
        self.url = f"{base_url}{ROUTE_API_ANNOTATIONS}"
        self.api_key = api_key

    @staticmethod
    def generate_event_data(audit_log_record: AuditLog) -> dict[str, Any]:
        return map_audit_log_record_to_grafana_annotation(audit_log_record)

    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def _track_event(self, event: dict[str, Any]) -> None:
        response = requests.post(
            url=self.url,
            headers=self._headers(),
            data=json.dumps(event),
        )

        logger.debug(
            "Sent event to Grafana. Response code was %s" % response.status_code
        )
