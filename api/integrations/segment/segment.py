import logging
import typing

from analytics.client import Client as SegmentClient
from environments.identities.models import Identity
from features.models import FeatureState
from integrations.common.wrapper import AbstractBaseIdentityIntegrationWrapper

from .models import SegmentConfiguration

logger = logging.getLogger(__name__)


class SegmentWrapper(AbstractBaseIdentityIntegrationWrapper):
    def __init__(self, config: SegmentConfiguration):
        api_key = config.api_key
        self.analytics = SegmentClient(write_key=api_key, sync_mode=True)

    def _identify_user(self, data: dict) -> None:
        self.analytics.identify(**data)
        logger.debug("Sent event to Segment.")

    def generate_user_data(
        self, identity: Identity, feature_states: typing.List[FeatureState]
    ) -> dict:
        feature_properties = {}

        for feature_state in feature_states:
            value = feature_state.get_feature_state_value(identity=identity)
            feature_properties[feature_state.feature.name] = (
                value if (feature_state.enabled and value) else feature_state.enabled
            )

        return {
            "user_id": identity.identifier,
            "traits": feature_properties,
        }
