import json
import logging
import time

from audit.models import AuditLog
from integrations.common.wrapper import AbstractBaseEventIntegrationWrapper

logger = logging.getLogger(__name__)

ANNOTATIONS_API_URI = "api/annotations"


class GrafanaWrapper(AbstractBaseEventIntegrationWrapper):
    def __init__(self, base_url: str, api_key: str) -> None:
        self.url = f"{base_url}{ANNOTATIONS_API_URI}"
        self.api_key = api_key

    @staticmethod
    def generate_event_data(audit_log_record: AuditLog) -> dict:
        log = audit_log_record.log
        email = audit_log_record.author_identifier

        epoch_time_in_milliseconds = round(time.time() * 1000)

        return {
            "text": f"{log} by user {email}",
            "dashboardUID": "",
            "tags": ["Flagsmith Event"],
            "time": epoch_time_in_milliseconds,
            "timeEnd": epoch_time_in_milliseconds,
        }

    def _headers(self) -> dict:
        return {
            "Content-Type": "application/json",
            "Authorization:": "Bearer %s" % self.api_key,
        }

    def _track_event(self, event: dict) -> None:
        response = self.session.post(
            f"{self.events_url}?api_key={self.api_key}", data=json.dumps(event)
        )
        logger.debug(
            "Sent event to DataDog. Response code was %s" % response.status_code
        )
