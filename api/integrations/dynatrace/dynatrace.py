import json
import logging

import requests

from integrations.common.wrapper import AbstractBaseEventIntegrationWrapper

logger = logging.getLogger(__name__)

EVENTS_API_URI = "api/v2/events/ingest"


class DynatraceWrapper(AbstractBaseEventIntegrationWrapper):
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.url = f"{self.base_url}{EVENTS_API_URI}?api-token={self.api_key}"

    def _track_event(self, event: dict) -> None:
        response = requests.post(self.url, data=json.dumps(event))
        logger.debug(
            "Sent event to Dynatrace. Response code was %s" % response.status_code
        )

    @staticmethod
    def generate_event_data(log: str, email: str, environment_name: str) -> dict:
        flag_properties = {
            "event": f"{log} by user {email}",
            "environment": environment_name,
        }

        return {
            "entitySelector": None,
            "title": "Flagsmith flag change.",
            "eventType": "CUSTOM_DEPLOYMENT",
            "properties": flag_properties,
        }
