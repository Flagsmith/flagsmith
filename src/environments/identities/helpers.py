from integrations.amplitude.amplitude import AmplitudeWrapper
from integrations.heap.heap import HeapWrapper
from integrations.mixpanel.mixpanel import MixpanelWrapper
from integrations.segment.segment import SegmentWrapper

IDENTITY_INTEGRATIONS = [
    {"relation_name": "amplitude_config", "wrapper": AmplitudeWrapper},
    {"relation_name": "segment_config", "wrapper": SegmentWrapper},
    {"relation_name": "heap_config", "wrapper": HeapWrapper},
    {"relation_name": "mixpanel_config", "wrapper": MixpanelWrapper},
]


def identify_integrations(identity, all_feature_states):
    for integration in IDENTITY_INTEGRATIONS:
        config = getattr(identity.environment, integration.get("relation_name"), None)
        api_key = getattr(config, "api_key", None)
        if api_key:
            wrapper = integration.get("wrapper")
            wrapper_instance = wrapper(api_key)
            user_data = wrapper_instance.generate_user_data(
                user_id=identity.identifier, feature_states=all_feature_states
            )
            wrapper_instance.identify_user_async(data=user_data)
