import requests

from core.constants import STRING
from django.contrib.contenttypes.models import ContentType
from environments.identities.traits.models import Trait
from environments.identities.traits.serializers import TraitSerializerBasic
from features.models import Feature, FeatureState
from integrations.common.models import IntegrationHealthRecord
from integrations.webhook.serializers import (
    IntegrationFeatureStateSerializer,
    SegmentSerializer,
)
from integrations.webhook.webhook import WebhookWrapper
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


def test_webhook_identify_user__records_health_status(  # type: ignore[no-untyped-def]
    mocker,
    integration_webhook_config,
):
    # Given
    webhook_wrapper = WebhookWrapper(integration_webhook_config)

    response = mocker.MagicMock(spec=requests.Response, status_code=200)

    def bool_true(self):
        return True

    response.__bool__ = bool_true.__get__(response)

    mocker.patch(
        "integrations.webhook.webhook.call_integration_webhook",
        return_value=response,
    )

    # When
    webhook_wrapper._identify_user({"identity": "identity-1"})

    # Then
    health_record = IntegrationHealthRecord.objects.get(
        object_id=integration_webhook_config.id,
        content_type=ContentType.objects.get_for_model(integration_webhook_config),
    )
    assert health_record.status_code == 200


def test_webhook_identify_user__unhealthy_status__records_health(
    mocker,
    integration_webhook_config,
):
    # Given
    webhook_wrapper = WebhookWrapper(integration_webhook_config)

    response = mocker.MagicMock(spec=requests.Response, status_code=500)

    def bool_true(self):
        return True

    response.__bool__ = bool_true.__get__(response)

    mocker.patch(
        "integrations.webhook.webhook.call_integration_webhook",
        return_value=response,
    )

    # When
    webhook_wrapper._identify_user({"identity": "identity-1"})

    # Then
    health_record = IntegrationHealthRecord.objects.get(
        object_id=integration_webhook_config.id,
        content_type=ContentType.objects.get_for_model(integration_webhook_config),
    )
    assert health_record.status_code == 500
