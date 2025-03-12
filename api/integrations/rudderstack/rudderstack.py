import logging
import typing

from rudderstack import analytics as rudder_analytics  # type: ignore[import-untyped]

from environments.identities.models import Identity
from environments.identities.traits.models import Trait
from features.models import FeatureState
from integrations.common.wrapper import AbstractBaseIdentityIntegrationWrapper

from .models import RudderstackConfiguration

logger = logging.getLogger(__name__)


class RudderstackWrapper(AbstractBaseIdentityIntegrationWrapper):  # type: ignore[type-arg]
    def __init__(self, config: RudderstackConfiguration):
        rudder_analytics.write_key = config.api_key
        rudder_analytics.dataPlaneUrl = config.base_url

    def _identify_user(self, user_data: dict) -> None:  # type: ignore[type-arg]
        rudder_analytics.identify(**user_data)

    def generate_user_data(
        self,
        identity: Identity,
        feature_states: typing.List[FeatureState],
        trait_models: typing.List[Trait] = None,  # type: ignore[assignment]
    ) -> dict:  # type: ignore[type-arg]
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
