from core.constants import STRING

from environments.identities.traits.models import Trait
from environments.identities.traits.serializers import TraitSerializerBasic
from features.models import Feature, FeatureState
from integrations.webhook.serializers import (
    IntegrationFeatureStateSerializer,
    SegmentSerializer,
)
from integrations.webhook.webhook import WebhookWrapper
from segments.models import Segment


def test_webhook_generate_user_data_generates_correct_data(
    integration_webhook_config, project, identity
):
    # Given
    Trait.objects.create(
        identity=identity,
        trait_key="trait_key",
        value_type=STRING,
        string_value="trait_value",
    )
    feature = Feature.objects.create(name="Test Feature", project=project)

    feature_states = FeatureState.objects.filter(feature=feature)
    expected_flags = IntegrationFeatureStateSerializer(
        feature_states, many=True, context={"identity": identity}
    ).data

    traits = Trait.objects.filter(identity=identity)
    expected_traits = TraitSerializerBasic(traits, many=True).data

    segments = Segment.objects.filter(project=project)
    expected_segments = SegmentSerializer(
        segments, many=True, context={"identity": identity}
    ).data
    expected_data = {
        "identity": identity.identifier,
        "traits": expected_traits,
        "segments": expected_segments,
        "flags": expected_flags,
    }
    webhook_wrapper = WebhookWrapper(integration_webhook_config)
    # When
    user_data = webhook_wrapper.generate_user_data(
        identity=identity, feature_states=feature_states
    )
    # Then
    assert expected_data == user_data
