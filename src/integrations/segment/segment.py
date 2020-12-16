import urllib.parse

import analytics as segment_analytics
import requests

from integrations.common.wrapper import AbstractBaseIdentityIntegrationWrapper
from util.logging import get_logger
from util.util import postpone

logger = get_logger(__name__)


class SegmentWrapper(AbstractBaseIdentityIntegrationWrapper):
    def __init__(self, api_key: str):
        self.analytics = segment_analytics
        self.analytics.write_key = api_key

    def _identify_user(self, data: dict) -> None:
        self.analytics.identify(**data)
        logger.debug(f"Sent event to Segment.")

    def generate_user_data(self, user_id, feature_states):
        return {
            "user_id": user_id,
            "traits": {
                feature_state.feature.name: feature_state.get_feature_state_value()
                if feature_state.get_feature_state_value() is not None
                else "None"
                for feature_state in feature_states
            },
        }
