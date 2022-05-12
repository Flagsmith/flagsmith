import logging
import typing

from environments.identities.traits.serializers import TraitSerializerBasic
from integrations.common.wrapper import AbstractBaseIdentityIntegrationWrapper
from webhooks.webhooks import call_integration_webhook

from .models import WebhookConfiguration
from .serializers import IntegrationFeatureStateSerializer, SegmentSerializer

if typing.TYPE_CHECKING:
    from environments.identities.models import Identity
    from environments.identities.traits.models import Trait
    from features.models import FeatureState

logger = logging.getLogger(__name__)


class WebhookWrapper(AbstractBaseIdentityIntegrationWrapper):
    def __init__(self, config: WebhookConfiguration):
        self.config = config

    def _identify_user(self, data: typing.Mapping) -> None:
        response = call_integration_webhook(self.config, data)
        logger.debug(
            "Sent event to Webhook. Response code was: %s" % response.status_code
        )

    def generate_user_data(
        self,
        identity: "Identity",
        feature_states: typing.List["FeatureState"],
        trait_models: typing.List["Trait"] = None,
    ) -> dict:
        serialized_flags = IntegrationFeatureStateSerializer(
            feature_states, many=True, context={"identity": identity}
        )
        serialized_traits = TraitSerializerBasic(
            trait_models or identity.identity_traits.all(), many=True
        )
        serialized_segments = SegmentSerializer(
            identity.environment.project.get_segments_from_cache(),
            many=True,
            context={"identity": identity},
        )

        data = {
            "identity": identity.identifier,
            "traits": serialized_traits.data,
            "flags": serialized_flags.data,
            "segments": serialized_segments.data,
        }
        return data
