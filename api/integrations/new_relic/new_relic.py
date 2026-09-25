import json
import logging

import requests

from audit.models import AuditLog
from integrations.common.services import record_integration_health
from integrations.common.wrapper import AbstractBaseEventIntegrationWrapper
from integrations.new_relic.models import NewRelicConfiguration

logger = logging.getLogger(__name__)

EVENTS_API_URI = "v2/applications/"


class NewRelicWrapper(AbstractBaseEventIntegrationWrapper):
    def __init__(self, config: NewRelicConfiguration):
        self.config = config
        self.base_url = (config.base_url or "").rstrip("/") + "/"
        self.api_key = config.api_key
        self.app_id = config.app_id
        self.url = f"{self.base_url}{EVENTS_API_URI}{self.app_id}/deployments.json"

    def _track_event(self, event: dict) -> None:  # type: ignore[type-arg]
        try:
            response = requests.post(
                self.url, headers=self._headers(), data=json.dumps(event), timeout=10
            )
        except requests.exceptions.RequestException:
            logger.warning("Failed to send event to NewRelic", exc_info=True)
            return

        try:
            record_integration_health(self.config, response.status_code)
        except Exception:
            logger.warning("Failed to record New Relic integration health")
        logger.debug(
            "Sent event to NewRelic. Response code was %s" % response.status_code
        )

    def _headers(self) -> dict:  # type: ignore[type-arg]
        return {"Content-Type": "application/json", "X-Api-Key": self.api_key}

    @staticmethod
    def generate_event_data(audit_log_record: AuditLog) -> dict:  # type: ignore[type-arg]
        log = audit_log_record.log
        environment_name = audit_log_record.environment_name
        email = audit_log_record.author_identifier

        return {
            "deployment": {
                "revision": f"env:{environment_name}",
                "changelog": f"{log} by user {email}",
                "description": "Flagsmith Feature Flag Event",
            }
        }
