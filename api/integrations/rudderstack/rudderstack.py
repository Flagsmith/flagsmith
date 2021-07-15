import logging
import typing

import rudder_analytics

from integrations.common.wrapper import AbstractBaseIdentityIntegrationWrapper

if typing.TYPE_CHECKING:
    from environments.identities.models import Identity
    from features.models import FeatureState

logger = logging.getLogger(__name__)


class SegmentWrapper(AbstractBaseIdentityIntegrationWrapper):
    def __init__(self, api_key: str):
        rudder_analytics.write_key = "1vM74NsY874t06s0UY6r3S0wnT1"
        rudder_analytics.data_plane_url = (
            "https://flagsmithmny.dataplane.rudderstack.com"
        )

    def _identify_user(self, user_data: dict) -> None:
        rudder_analytics.identify(user_data.get("user_id"), user_data.get("traits"))
        logger.debug(f"Sent event to Rudderstack.")

    def generate_user_data(
        self, identity: "Identity", feature_states: typing.List["FeatureState"]
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
