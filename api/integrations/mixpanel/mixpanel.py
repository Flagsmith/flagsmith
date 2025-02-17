import logging
import typing

import requests

from environments.identities.models import Identity
from environments.identities.traits.models import Trait
from features.models import FeatureState
from integrations.common.wrapper import AbstractBaseIdentityIntegrationWrapper

from .models import MixpanelConfiguration

MixpanelUserData: typing.TypeAlias = list[dict[str, typing.Any]]


logger = logging.getLogger(__name__)

MIXPANEL_API_URL = "https://api.mixpanel.com"


class MixpanelWrapper(AbstractBaseIdentityIntegrationWrapper[MixpanelUserData]):
    def __init__(self, config: MixpanelConfiguration):
        self.api_key = config.api_key
        self.url = f"{MIXPANEL_API_URL}/engage#profile-set"

        # Pass the integration ID as per https://developer.mixpanel.com/docs/partner-integration-id
        self.headers = {
            "Accept": "text/plain",
            "X-Mixpanel-Integration-ID": "flagsmith",
        }

    def _identify_user(self, user_data: MixpanelUserData) -> None:
        response = requests.post(self.url, headers=self.headers, json=user_data)
        logger.debug(
            "Sent event to Mixpanel. Response code was: %s" % response.status_code
        )
        logger.debug("Sent event to Mixpanel. Response content was: %s" % response.text)

    def generate_user_data(
        self,
        identity: Identity,
        feature_states: typing.List[FeatureState],
        trait_models: typing.List[Trait],
    ) -> MixpanelUserData:
        feature_properties = {}

        for feature_state in feature_states:
            value = feature_state.get_feature_state_value(identity=identity)
            feature_properties[feature_state.feature.name] = (
                value if (feature_state.enabled and value) else feature_state.enabled
            )

        return [
            {
                "$token": self.api_key,
                "$distinct_id": identity.identifier,
                "$set": feature_properties,
                "$ip": "0",
            }
        ]
