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

    def _identify_user(self, user_data: dict) -> None:
        response = requests.post(self.url, data=user_data)
        logger.debug("Sent event to Amplitude. Response code was: %s" % response.status_code)

    @postpone
    def identify_user_async(self, user_data: dict) -> None:
        self._identify_user(user_data)

    def generate_user_data(self, user_id, feature_states):

        user_data = {
            "api_key": self.api_key,
            "identification": {
                "user_id": user_id,
                "user_properties": json.dumps({
                    feature_state.feature.name: feature_state.get_feature_state_value()
                    for feature_state in feature_states
                })
            }
        }

        return user_data
