import json
import logging
import urllib.parse

import requests

from integrations.common.wrapper import AbstractBaseIdentityIntegrationWrapper
from util.util import postpone

logger = logging.getLogger(__name__)

AMPLITUDE_API_URL = "https://api.amplitude.com"


class AmplitudeWrapper(AbstractBaseIdentityIntegrationWrapper):
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.url = f"{AMPLITUDE_API_URL}/identify"

    def _identify_user(self, user_data: dict) -> None:
        payload = {"api_key": self.api_key, "identification": json.dumps([user_data])}

        response = requests.post(self.url, data=payload)
        logger.debug(
            "Sent event to Amplitude. Response code was: %s" % response.status_code
        )

    def generate_user_data(self, user_id, feature_states):
        feature_properties = {}

        for feature_state in feature_states:
            value = feature_state.get_feature_state_value()
            feature_properties[feature_state.feature.name] = (
                value if (feature_state.enabled and value) else feature_state.enabled
            )

        return {
            "user_id": user_id,
            "user_properties": feature_properties,
        }
