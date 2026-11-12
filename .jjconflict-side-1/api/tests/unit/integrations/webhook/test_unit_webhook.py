import pytest
from pytest_django import DjangoAssertNumQueries

from core.constants import STRING
from environments.identities.models import Identity
from environments.identities.traits.models import Trait
from environments.identities.traits.serializers import TraitSerializerBasic
from evaluation.services import get_identity_feature_states
from features.models import Feature
from integrations.webhook.models import WebhookConfiguration
from integrations.webhook.serializers import (
    IntegrationFeatureStateSerializer,
    SegmentSerializer,
)
from integrations.webhook.webhook import WebhookWrapper
from projects.models import Project
from segments.models import Segment


def test_webhook_generate_user_data__with_identity_and_features__returns_correct_data(  # type: ignore[no-untyped-def]
    integration_webhook_config, project, identity
):
    # Given
    Trait.objects.create(
        identity=identity,
        trait_key="trait_key",
        value_type=STRING,
        string_value="trait_value",
    )
    Feature.objects.create(name="Test Feature", project=project)

    feature_states = get_identity_feature_states(identity)
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


def test_webhook_generate_user_data__trait_models_provided__uses_trait_models_argument(  # type: ignore[no-untyped-def]
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


@pytest.mark.parametrize("segment_count", [1, 10])
def test_webhook_generate_user_data__any_number_of_segments__evaluates_membership_once(
    segment_count: int,
    identity: Identity,
    project: Project,
    integration_webhook_config: WebhookConfiguration,
    django_assert_num_queries: DjangoAssertNumQueries,
) -> None:
    # Given
    for i in range(segment_count):
        Segment.objects.create(name=f"segment_{i}", project=project)
    webhook_wrapper = WebhookWrapper(integration_webhook_config)

    # When / Then
    with django_assert_num_queries(7):
        webhook_wrapper.generate_user_data(identity=identity, feature_states=[])
