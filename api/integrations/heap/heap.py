import logging
import typing

import requests

from environments.identities.models import Identity
from environments.identities.traits.models import Trait
from features.models import FeatureState
from integrations.common.services import record_integration_health
from integrations.common.wrapper import AbstractBaseIdentityIntegrationWrapper

from .constants import DEFAULT_HEAP_API_URL
from .models import HeapConfiguration

logger = logging.getLogger(__name__)


class HeapWrapper(AbstractBaseIdentityIntegrationWrapper):  # type: ignore[type-arg]
    def __init__(self, config: HeapConfiguration):
        self.config = config
        self.api_key = config.api_key
        base_url = (config.base_url or DEFAULT_HEAP_API_URL).rstrip("/")
        self.url = f"{base_url}/api/track"

    def _identify_user(self, user_data: dict) -> None:  # type: ignore[type-arg]
        response = requests.post(self.url, json=user_data, timeout=10)

        try:
            record_integration_health(self.config, response.status_code)
        except Exception:
            logger.warning("Failed to record Heap integration health")
        logger.debug("Sent event to Heap. Response code was: %s" % response.status_code)

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
                value
                if (feature_state.enabled and value is not None)
                else feature_state.enabled
            )

        return {
            "app_id": self.api_key,
            "identity": identity.identifier,
            "event": "Flagsmith Feature Flags",
            "properties": feature_properties,
        }
