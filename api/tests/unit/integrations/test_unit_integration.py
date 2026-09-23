from functools import reduce
from operator import getitem
from typing import Any

import pytest

from environments.identities.models import Identity
from environments.models import Environment
from evaluation.services import get_identity_feature_states
from features.models import Feature, FeatureState
from features.multivariate.models import MultivariateFeatureStateValue
from integrations.amplitude.amplitude import AmplitudeWrapper
from integrations.amplitude.models import AmplitudeConfiguration
from integrations.common.models import EnvironmentIntegrationModel
from integrations.common.wrapper import AbstractBaseIdentityIntegrationWrapper
from integrations.heap.heap import HeapWrapper
from integrations.heap.models import HeapConfiguration
from integrations.integration import identify_integrations
from integrations.mixpanel.mixpanel import MixpanelWrapper
from integrations.mixpanel.models import MixpanelConfiguration
from integrations.rudderstack.models import RudderstackConfiguration
from integrations.rudderstack.rudderstack import RudderstackWrapper
from integrations.segment.models import SegmentConfiguration
from integrations.segment.segment import SegmentWrapper


def test_identify_integrations__amplitude_configured__calls_amplitude(  # type: ignore[no-untyped-def]
    mocker, environment, identity
):
    # Given
    mock_amplitude_wrapper = mocker.patch(
        "integrations.amplitude.amplitude.AmplitudeWrapper.identify_user_async"
    )
    AmplitudeConfiguration.objects.create(api_key="abc-123", environment=environment)

    # When
    identify_integrations(identity, get_identity_feature_states(identity))  # type: ignore[no-untyped-call]

    # Then
    mock_amplitude_wrapper.assert_called()


def test_identify_integrations__segment_configured__calls_segment(  # type: ignore[no-untyped-def]
    mocker, environment, identity
):
    # Given
    mock_segment_wrapper = mocker.patch(
        "integrations.segment.segment.SegmentWrapper.identify_user_async"
    )
    SegmentConfiguration.objects.create(api_key="abc-123", environment=environment)
    # When
    identify_integrations(identity, get_identity_feature_states(identity))  # type: ignore[no-untyped-call]

    # Then
    mock_segment_wrapper.assert_called()


def test_identify_integrations__multiple_integrations__calls_all(  # type: ignore[no-untyped-def]
    mocker, identity
):
    # Given
    integration_wrapper_a = mocker.MagicMock(
        autospec=AbstractBaseIdentityIntegrationWrapper
    )
    integration_wrapper_b = mocker.MagicMock(
        autospec=AbstractBaseIdentityIntegrationWrapper
    )

    integration_a_config = mocker.MagicMock(
        autospec=EnvironmentIntegrationModel, deleted=False
    )
    integration_b_config = mocker.MagicMock(
        autospec=EnvironmentIntegrationModel, deleted=False
    )

    identity.environment.integration_a_config = integration_a_config
    identity.environment.integration_b_config = integration_b_config

    identity_integrations = [
        {"relation_name": "integration_a_config", "wrapper": integration_wrapper_a},
        {"relation_name": "integration_b_config", "wrapper": integration_wrapper_b},
    ]
    mocker.patch(
        "integrations.integration.IDENTITY_INTEGRATIONS", identity_integrations
    )

    # When
    identify_integrations(identity, get_identity_feature_states(identity))  # type: ignore[no-untyped-call]

    # Then
    # Integration a was successfully called

    integration_wrapper_a.assert_called_with(integration_a_config)

    integration_a_mocked_generate_user_data = (
        integration_wrapper_a.return_value.generate_user_data
    )

    integration_a_mocked_generate_user_data.assert_called_with(
        identity=identity,
        feature_states=get_identity_feature_states(identity),
        trait_models=None,
    )
    integration_wrapper_a.return_value.identify_user_async.assert_called_with(
        data=integration_a_mocked_generate_user_data.return_value
    )

    # Integration b was successfully called
    integration_wrapper_b.assert_called_with(integration_b_config)

    integration_b_mocked_generate_user_data = (
        integration_wrapper_b.return_value.generate_user_data
    )

    integration_b_mocked_generate_user_data.assert_called_with(
        identity=identity,
        feature_states=get_identity_feature_states(identity),
        trait_models=None,
    )
    integration_wrapper_b.return_value.identify_user_async.assert_called_with(
        data=integration_b_mocked_generate_user_data.return_value
    )


def test_identify_integrations__deleted_integration__does_not_call(  # type: ignore[no-untyped-def]
    mocker, environment, identity
):
    # Given
    mock_segment_wrapper = mocker.patch(
        "integrations.segment.segment.SegmentWrapper.identify_user_async"
    )

    sc = SegmentConfiguration.objects.create(api_key="abc-123", environment=environment)
    sc.delete()

    # When
    identify_integrations(identity, get_identity_feature_states(identity))  # type: ignore[no-untyped-call]

    # Then
    mock_segment_wrapper.assert_not_called()


@pytest.mark.parametrize(
    "wrapper_class, configuration_class, flags_path",
    [
        (AmplitudeWrapper, AmplitudeConfiguration, ("user_properties",)),
        (HeapWrapper, HeapConfiguration, ("properties",)),
        (MixpanelWrapper, MixpanelConfiguration, (0, "$set")),
        (RudderstackWrapper, RudderstackConfiguration, ("traits",)),
        (SegmentWrapper, SegmentConfiguration, ("traits",)),
    ],
)
def test_generate_user_data__multivariate_identity_override__reports_evaluated_value(
    wrapper_class: type[AbstractBaseIdentityIntegrationWrapper[Any]],
    configuration_class: type[EnvironmentIntegrationModel],
    flags_path: tuple[int | str, ...],
    environment: Environment,
    identity: Identity,
    multivariate_feature: Feature,
) -> None:
    # Given
    option = multivariate_feature.multivariate_options.order_by("id").last()
    assert option
    identity_override = FeatureState.objects.create(
        feature=multivariate_feature,
        environment=environment,
        identity=identity,
        enabled=True,
    )
    MultivariateFeatureStateValue.objects.create(
        feature_state=identity_override,
        multivariate_feature_option=option,
        percentage_allocation=100,
    )
    wrapper = wrapper_class(  # type: ignore[call-arg]
        configuration_class(api_key="api-key", base_url="https://example.com")
    )

    # When
    user_data = wrapper.generate_user_data(
        identity=identity,
        feature_states=get_identity_feature_states(identity),
        trait_models=[],
    )

    # Then
    assert reduce(getitem, flags_path, user_data) == {
        multivariate_feature.name: option.value
    }
