import json
import logging

import requests

from audit.models import AuditLog
from integrations.common.wrapper import AbstractBaseEventIntegrationWrapper

logger = logging.getLogger(__name__)

EVENTS_API_URI = "v2/applications/"


class NewRelicWrapper(AbstractBaseEventIntegrationWrapper):
    def __init__(self, base_url: str, api_key: str, app_id: str):
        self.base_url = base_url
        self.api_key = api_key
        self.app_id = app_id
        self.url = f"{self.base_url}{EVENTS_API_URI}{self.app_id}/deployments.json"

    def _track_event(self, event: dict) -> None:
        response = requests.post(
            self.url, headers=self._headers(), data=json.dumps(event)
        )
        logger.debug(
            "Sent event to NewRelic. Response code was %s" % response.status_code
        )

    def _headers(self) -> dict:
        return {"Content-Type": "application/json", "X-Api-Key": self.api_key}

    @staticmethod
    def generate_event_data(audit_log_record: AuditLog) -> dict:
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
