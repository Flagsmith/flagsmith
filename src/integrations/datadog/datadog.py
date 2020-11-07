import json

import requests
from util.logging import get_logger
from util.util import postpone

logger = get_logger(__name__)

EVENTS_API_URI = "api/v1/events"


class DataDogWrapper:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.url = f"{self.base_url}{EVENTS_API_URI}?api_key={self.api_key}"

    def _track_event(self, event: dict) -> None:
        response = requests.post(self.url, data=json.dumps(event))
        logger.debug("Sent event to DataDog. Response code was %s" % response.status_code)

    @postpone
    def track_event_async(self, event: dict) -> None:
        self._track_event(event)

    @staticmethod
    def generate_event_data(log: str, email: str, environment_name: str):
        event_data = {
            "text": f"{log} by user {email}",
            "title": "Bullet Train Feature Flag Event",
            "tags": [f"env:{environment_name}"]
        }

        return event_data
