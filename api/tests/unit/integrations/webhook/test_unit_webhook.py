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


def test_webhook_generate_user_data_generates_correct_data(  # type: ignore[no-untyped-def]
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


def test_webhook_wrapper_generate_user_data_uses_trait_models_argument_when_provided(  # type: ignore[no-untyped-def]
    identity, project, integration_webhook_config
):
    # Given
    unsaved_trait = Trait(
        identity=identity,
        trait_key="trait_key",
        value_type=STRING,
        string_value="trait_value",
    )
    expected_traits = TraitSerializerBasic([unsaved_trait], many=True).data

    expected_data = {
        "identity": identity.identifier,
        "traits": expected_traits,
        "segments": [],
        "flags": [],
    }
    webhook_wrapper = WebhookWrapper(integration_webhook_config)

    # When
    user_data = webhook_wrapper.generate_user_data(
        identity=identity, feature_states=[], trait_models=[unsaved_trait]
    )

    # Then
    assert expected_data == user_data
