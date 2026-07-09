import json
import logging
from typing import Any

import requests

from audit.models import AuditLog
from integrations.common.services import record_integration_health
from integrations.common.wrapper import AbstractBaseEventIntegrationWrapper
from integrations.grafana.mappers import (
    map_audit_log_record_to_grafana_annotation,
)
from integrations.grafana.models import (
    GrafanaOrganisationConfiguration,
    GrafanaProjectConfiguration,
)

logger = logging.getLogger(__name__)

ROUTE_API_ANNOTATIONS = "/api/annotations"


class GrafanaWrapper(AbstractBaseEventIntegrationWrapper):
    def __init__(
        self,
        config: GrafanaProjectConfiguration | GrafanaOrganisationConfiguration,
    ) -> None:
        self.config = config
        base_url = (
            config.base_url[:-1] if config.base_url.endswith("/") else config.base_url
        )
        self.url = f"{base_url}{ROUTE_API_ANNOTATIONS}"
        self.api_key = config.api_key

    @staticmethod
    def generate_event_data(audit_log_record: AuditLog) -> dict[str, Any]:
        return map_audit_log_record_to_grafana_annotation(audit_log_record)  # type: ignore[return-value]

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

        try:
            record_integration_health(self.config, response.status_code)
        except Exception:
            logger.warning("Failed to record Grafana integration health")
        logger.debug(
            "Sent event to Grafana. Response code was %s" % response.status_code
        )
