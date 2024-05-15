from typing import Type, TypedDict

from environments.constants import IDENTITY_INTEGRATIONS_RELATION_NAMES
from integrations.amplitude.amplitude import AmplitudeWrapper
from integrations.common.wrapper import AbstractBaseIdentityIntegrationWrapper
from integrations.heap.heap import HeapWrapper
from integrations.mixpanel.mixpanel import MixpanelWrapper
from integrations.rudderstack.rudderstack import RudderstackWrapper
from integrations.segment.segment import SegmentWrapper
from integrations.webhook.webhook import WebhookWrapper


class IntegrationConfig(TypedDict):
    relation_name: str
    wrapper: Type[AbstractBaseIdentityIntegrationWrapper]


IDENTITY_INTEGRATIONS: list[IntegrationConfig] = [
    {"relation_name": "amplitude_config", "wrapper": AmplitudeWrapper},
    {"relation_name": "heap_config", "wrapper": HeapWrapper},
    {"relation_name": "mixpanel_config", "wrapper": MixpanelWrapper},
    {"relation_name": "rudderstack_config", "wrapper": RudderstackWrapper},
    {"relation_name": "segment_config", "wrapper": SegmentWrapper},
    {"relation_name": "webhook_config", "wrapper": WebhookWrapper},
]

assert set(IDENTITY_INTEGRATIONS_RELATION_NAMES) == (
    _configured_integrations := {
        integration_config["relation_name"]
        for integration_config in IDENTITY_INTEGRATIONS
    }
), (
    "Check that `environments.constants.IDENTITY_INTEGRATIONS_RELATION_NAMES` and "
    "`integration.integration.IDENTITY_INTEGRATIONS` contain the same values. \n"
    f"Unconfigured integrations: {set(IDENTITY_INTEGRATIONS_RELATION_NAMES) - _configured_integrations}"
)


def identify_integrations(identity, all_feature_states, trait_models=None):
    for integration in IDENTITY_INTEGRATIONS:
        config = getattr(identity.environment, integration.get("relation_name"), None)
        if config and not config.deleted:
            wrapper = integration.get("wrapper")
            wrapper_instance = wrapper(config)
            user_data = wrapper_instance.generate_user_data(
                identity=identity,
                feature_states=all_feature_states,
                trait_models=trait_models,
            )
            wrapper_instance.identify_user_async(data=user_data)
