import logging
import typing

from analytics.client import Client as SegmentClient  # type: ignore[import-untyped]

from environments.identities.models import Identity
from environments.identities.traits.models import Trait
from evaluation.types import EvaluatedFeatureState
from integrations.common.mappers import map_feature_states_to_feature_properties
from integrations.common.wrapper import AbstractBaseIdentityIntegrationWrapper

from .models import SegmentConfiguration

logger = logging.getLogger(__name__)


class SegmentWrapper(AbstractBaseIdentityIntegrationWrapper):  # type: ignore[type-arg]
    def __init__(self, config: SegmentConfiguration):
        self.analytics = SegmentClient(
            write_key=config.api_key, sync_mode=True, host=config.base_url
        )

    def _identify_user(self, data: dict) -> None:  # type: ignore[type-arg]
        self.analytics.identify(**data)

    def generate_user_data(
        self,
        identity: Identity,
        feature_states: typing.List[EvaluatedFeatureState],
        trait_models: typing.List[Trait] = None,  # type: ignore[assignment]
    ) -> dict:  # type: ignore[type-arg]
        feature_properties = map_feature_states_to_feature_properties(feature_states)

        return {
            "user_id": identity.identifier,
            "traits": feature_properties,
        }
