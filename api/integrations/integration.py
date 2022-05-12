from integrations.amplitude.amplitude import AmplitudeWrapper
from integrations.heap.heap import HeapWrapper
from integrations.mixpanel.mixpanel import MixpanelWrapper
from integrations.rudderstack.rudderstack import RudderstackWrapper
from integrations.segment.segment import SegmentWrapper
from integrations.webhook.webhook import WebhookWrapper

IDENTITY_INTEGRATIONS = [
    {"relation_name": "amplitude_config", "wrapper": AmplitudeWrapper},
    {"relation_name": "segment_config", "wrapper": SegmentWrapper},
    {"relation_name": "heap_config", "wrapper": HeapWrapper},
    {"relation_name": "mixpanel_config", "wrapper": MixpanelWrapper},
    {"relation_name": "webhook_config", "wrapper": WebhookWrapper},
    {"relation_name": "rudderstack_config", "wrapper": RudderstackWrapper},
]


def identify_integrations(identity, all_feature_states, trait_models=None):
    for integration in IDENTITY_INTEGRATIONS:
        config = getattr(identity.environment, integration.get("relation_name"), None)
        if config:
            wrapper = integration.get("wrapper")
            wrapper_instance = wrapper(config)
            user_data = wrapper_instance.generate_user_data(
                identity=identity,
                feature_states=all_feature_states,
                trait_models=trait_models,
            )
            wrapper_instance.identify_user_async(data=user_data)
