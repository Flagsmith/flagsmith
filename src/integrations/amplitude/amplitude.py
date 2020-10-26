import json

import requests

from util.logging import get_logger
from util.util import postpone

logger = get_logger(__name__)

AMPLITUDE_API_URL = "https://api.amplitude.com"


class AmplitudeWrapper:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.url = f"{AMPLITUDE_API_URL}/identify"

    def _identify_user(self, user_id: str, **user_properties) -> None:
        data = {
            "api_key": self.api_key,
            "identification": {
                "user_id": user_id,
                "user_properties": json.dumps({**user_properties})
            }
        }
        response = requests.post(self.url, data=data)
        logger.debug("Sent event to Amplitude. Response code was: %s" % response.status_code)

    @postpone
    def identify_user_async(self, user_id: str, **user_properties) -> None:
        return self._identify_user(user_id, **user_properties)
