import json
import logging

import requests

from audit.models import AuditLog
from integrations.common.services import record_integration_health
from integrations.common.wrapper import AbstractBaseEventIntegrationWrapper
from integrations.datadog.models import DataDogConfiguration

logger = logging.getLogger(__name__)

EVENTS_API_URI = "api/v1/events"
FLAGSMITH_SOURCE_TYPE_NAME = "flagsmith"


class DataDogWrapper(AbstractBaseEventIntegrationWrapper):
    def __init__(
        self,
        config: DataDogConfiguration,
        session: requests.Session = None,  # type: ignore[assignment]
    ) -> None:
        self.config = config
        self.base_url = (config.base_url or "").rstrip("/") + "/"
        self.events_url = f"{self.base_url}{EVENTS_API_URI}"
        self.use_custom_source = config.use_custom_source

        self.api_key = config.api_key
        self.session = session or requests.Session()

    @staticmethod
    def generate_event_data(audit_log_record: AuditLog) -> dict:  # type: ignore[type-arg]
        log = audit_log_record.log
        environment_name = audit_log_record.environment_name
        email = audit_log_record.author_identifier

        return {
            "text": f"{log} by user {email}",
            "title": "Flagsmith Feature Flag Event",
            "tags": [f"env:{environment_name}"],
        }

    def _track_event(self, event: dict) -> None:  # type: ignore[type-arg]
        if self.use_custom_source:
            event["source_type_name"] = FLAGSMITH_SOURCE_TYPE_NAME

        response = self.session.post(
            f"{self.events_url}?api_key={self.api_key}", data=json.dumps(event)
        )

        try:
            record_integration_health(self.config, response.status_code)
        except Exception:
            logger.warning("Failed to record DataDog integration health")
        logger.debug(
            "Sent event to DataDog. Response code was %s" % response.status_code
        )
