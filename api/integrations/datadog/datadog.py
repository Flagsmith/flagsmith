import json
import logging

import requests

from integrations.common.wrapper import AbstractBaseEventIntegrationWrapper

logger = logging.getLogger(__name__)

EVENTS_API_URI = "api/v1/events"


class DataDogWrapper(AbstractBaseEventIntegrationWrapper):
    def __init__(self, base_url: str, api_key: str, session: requests.Session = None):
        self.base_url = base_url
        if self.base_url[-1] != "/":
            self.base_url += "/"
        self.events_url = f"{self.base_url}{EVENTS_API_URI}"

        self.api_key = api_key
        self.session = session or requests.Session()

    @staticmethod
    def generate_event_data(log: str, email: str, environment_name: str) -> dict:
        return {
            "text": f"{log} by user {email}",
            "title": "Flagsmith Feature Flag Event",
            "tags": [f"env:{environment_name}"],
        }

    def _track_event(self, event: dict) -> None:
        response = self.session.post(
            f"{self.events_url}?api_key={self.api_key}", data=json.dumps(event)
        )
        logger.debug(
            "Sent event to DataDog. Response code was %s" % response.status_code
        )
